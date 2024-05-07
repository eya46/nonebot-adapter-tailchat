import json
from asyncio import TimeoutError as AsyncTimeoutError
from asyncio import create_task, gather, sleep, wait_for
from functools import partial
from traceback import print_exc
from typing import Any, Optional

from nonebot import escape_tag, get_plugin_config
from nonebot.adapters import Adapter as BaseAdapter
from nonebot.drivers import Driver
from nonebot.internal.driver import ContentTypes, HTTPClientMixin, Request, Response
from typing_extensions import override
from yarl import URL

from .bot import Bot
from .config import BotInfo, Config
from .const import ADAPTER_NAME
from .event import EVENT_CLASSES, Event
from .exception import ActionFailed, DisconnectException
from .message import Message
from .util import log, retry


class Adapter(BaseAdapter):
    @override
    def __init__(self, driver: Driver, **kwargs: Any):
        super().__init__(driver, **kwargs)
        self.adapter_config: Config = get_plugin_config(Config)
        self.tasks = []
        self.on_ready(self._setup)
        self.on_ready(Message.update_parser)
        self.driver.on_shutdown(self._shutdown)
        self.is_http_client_driver = isinstance(self.driver, HTTPClientMixin)

    @classmethod
    @override
    def get_name(cls) -> str:
        return ADAPTER_NAME

    @override
    async def _call_api(self, bot: Bot, api: str, **data: Any) -> Any:
        use_http = data.get("use_http_", bot.base_info.useHttp)  # 使用http
        use_sio = data.get("use_sio_", not use_http)  # 使用socketio
        use_api = data.get("use_api_", True)  # url / 'api' / api
        if not bot.base_info.useHttp and (not use_sio or use_http):
            log("WARNING", f"use_http is False, but api <y>{api}</y> use / strictly.")
        if use_http or not use_sio:
            if not self.is_http_client_driver:
                raise RuntimeError("HTTPClientMixin is required when use http")
            self.driver: HTTPClientMixin
            resp = await self.driver.request(
                Request(
                    "POST",
                    str((URL(bot.url) / "api" if use_api else URL(bot.url)) / api),
                    json=data,
                    headers={"X-Token": bot.base_info.jwt or ""},
                )
            )
            data = self._loads(resp.content)
            self._handle_http_api(resp, data)
        else:
            data = await bot.sio.call(api, data)
            self._handle_socketio_api(data)
        return data.get("data")

    async def _setup(self):
        if any(i.useHttp for i in self.adapter_config.bots_info) and not self.is_http_client_driver:
            raise RuntimeError("HTTPClientMixin is required when use http")
        for i in self.adapter_config.bots_info:
            self.tasks.append(
                create_task(
                    # 防止因 socketio/tailchat 奇怪错误导致的异常
                    retry(self.adapter_config.reconnect_interval, self._handle_bot)(i),
                    name=f"handle_bot_{i.appId}",
                )
            )

    async def _shutdown(self):
        for task in self.tasks:
            if not task.done():
                task.cancel()

        await gather(*self.tasks, return_exceptions=True)

    async def _handle_bot(self, bot_info: BotInfo):
        first = True
        connected = False
        added = False

        async def _wait():  # 确保断连后打断wait
            nonlocal connected
            while True:
                if not connected:
                    raise DisconnectException()
                await sleep(1)

        def _check():
            nonlocal connected
            connected = False

        bot = Bot(self, bot_info.appId, bot_info)
        bot.sio.on("*", partial(self._handle_event, bot))
        bot.sio.on("disconnect", _check)
        while True:
            try:
                await wait_for(bot.login(bot.base_info.jwt), self.adapter_config.time_out)
                if first:
                    await wait_for(self._connect_bot(bot, first), self.adapter_config.time_out)
                    first = False
                await bot.update_info(bot.base_info.jwt)
                if not added:
                    self._bot_connect(bot)
                    added = True
                connected = True
                await gather(bot.sio.wait(), _wait())
            except DisconnectException:
                log.warning(f"Bot {escape_tag(str(bot))} socketio connection closed")
            except AsyncTimeoutError:
                log.warning(f"Bot {escape_tag(str(bot))} connection timeout")
            except Exception as e:
                log.error(f"Error when _handle_bot: {repr(e)}")
                print_exc()
            connected = False
            if added:
                self._bot_disconnect(bot)
                added = False
            log.debug(f"Bot {escape_tag(str(bot))} will reconnect in {self.adapter_config.reconnect_interval} seconds")
            await sleep(self.adapter_config.reconnect_interval)

    def _bot_connect(self, bot: Bot):
        try:
            self.bot_connect(bot)
        except Exception as e:
            log.trace(f"Error when bot_connect: {repr(e)}")

    def _bot_disconnect(self, bot: Bot):
        try:
            self.bot_disconnect(bot)
        except Exception as e:
            log.trace(f"Error when bot_disconnect: {repr(e)}")

    @staticmethod
    async def _connect_bot(bot: Bot, first: bool = True):
        if first:
            log.debug(f"try to connect bot {escape_tag(str(bot))}")
            await bot.connect()
        else:
            log.info(f"try to reconnect bot {escape_tag(str(bot))}")
        log.success(f"<y>Bot {escape_tag(str(bot))}</y> connected")
        await bot.sio.emit("chat.converse.findAndJoinRoom")

    @staticmethod
    async def _handle_event(bot: Bot, event: str, data: dict, _: Optional[any] = None):
        model = EVENT_CLASSES.get(event)
        log.trace(f"Event: {event}, MatchModel: {model}, Data: {data}")
        data["event_name"] = event
        data["self_id"] = bot.self_id
        await bot.handle_event((model or Event).model_validate(data))

    @staticmethod
    def _loads(data: ContentTypes) -> Any:
        try:
            return json.loads(data)
        except json.JSONDecodeError:
            log.error("Error when loads data", escape_tag(data.decode() if isinstance(data, bytes) else str(data)))
            raise

    @staticmethod
    def _handle_http_api(resp: Response, data: dict):
        if resp.status_code != 200:
            raise ActionFailed(message=f'{data.get("name", "unknown")}:{data.get("message")}', code=resp.status_code)

    @staticmethod
    def _handle_socketio_api(data: dict):
        if not data.get("result", True):
            raise ActionFailed(message=f'{data.get("name", "unknown")}:{data.get("message")}', code=data.get("code"))
