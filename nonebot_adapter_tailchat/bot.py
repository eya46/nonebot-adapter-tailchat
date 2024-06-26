from asyncio import sleep
from base64 import urlsafe_b64decode
from functools import wraps
from hashlib import md5
from json import loads
from time import time
from typing import TYPE_CHECKING, Optional, Union

from pydantic import TypeAdapter
from socketio import AsyncClient as AsyncSocketClient

from .api import API
from .config import BotInfo
from .const import Undefined
from .event import Event, MessageEvent
from .message import Message, MessageSegment
from .model import (
    BaseBotInfo,
    FileInfo,
    JwtPayload,
    MessageRet,
    TokenInfo,
)
from .util import log

if TYPE_CHECKING:
    from .adapter import Adapter


def _with_update_info(func):
    @wraps(func)
    async def wrapper(self: "Bot", *args, **kwargs):
        _ = await func(self, *args, **kwargs)
        await self.update_info(self.base_info.jwt)
        return _

    return wrapper


class Bot(API):
    def __str__(self):
        return f"{self.info.nickname}-{self.self_id}" if self.info else self.self_id

    async def connect(self):
        return await self.sio.connect(
            url=self.url,
            auth={"token": self.base_info.jwt},
            transports=["websocket"],
        )

    @staticmethod
    def md5(text: str) -> str:
        return md5(text.encode()).hexdigest()

    @staticmethod
    def decode_jwt(jwt: str) -> tuple[dict, JwtPayload, str]:
        segments = jwt.split(".")
        if len(segments) != 3:
            raise ValueError("Invalid JWT format.")

        return (
            loads(urlsafe_b64decode(segments[0] + "===").decode("utf-8")),
            JwtPayload.model_validate(loads(urlsafe_b64decode(segments[1] + "===").decode("utf-8"))),
            segments[2],
        )

    @classmethod
    async def build(cls, adapter: "Adapter", base_info: BotInfo):
        bot = Bot(adapter, base_info.appId, base_info)
        await bot.login(base_info.jwt)
        return bot

    async def update_info(self, jwt: Optional[str]):
        jwt = jwt or self.base_info.jwt
        self.info = await self.resolveToken(token=jwt)
        self.base_info.jwt = jwt
        self.self_id = self.info.userId

    def __init__(self, adapter: "Adapter", self_id: str, base_info: BotInfo):
        super().__init__(adapter, self_id)
        self.url = str(base_info.url)
        self.base_info = base_info
        self.sio = AsyncSocketClient(serializer="msgpack")
        self.info: Optional[TokenInfo] = None

    async def send(
        self,
        event: Event,
        message: Union[str, Message, MessageSegment],
        encode: bool = False,
        **kwargs,
    ) -> MessageRet:
        if not isinstance(event, MessageEvent):
            raise ValueError("event must be MessageEvent")
        return await self.sendMessage(
            content=(Message(message).decode() if encode else message)
            if isinstance(message, str)
            else message.decode(),
            converseId=event.get_converse_id(),
            groupId=event.get_group_id() or Undefined,
            meta=kwargs.get("meta", Undefined),
            plain=kwargs.get("plain", Undefined),
        )

    async def loginBot(self, *, appId: str, appSecret: str) -> BaseBotInfo:
        return TypeAdapter(BaseBotInfo).validate_python(
            await self.call_api(
                "openapi.bot.login", token=self.md5(appId + appSecret), appId=appId, use_http_=True, use_sio_=False
            )
        )

    @_with_update_info
    async def login(self, jwt: Optional[str] = None):
        if jwt:
            jwt_data = self.decode_jwt(jwt)[1]
            if (jwt_data.exp.timestamp() - time()) > 3600:
                self.base_info.jwt = jwt
                return
        if self.base_info.appId and self.base_info.appSecret:
            data = await self.loginBot(appId=self.base_info.appId, appSecret=self.base_info.appSecret)
            self.base_info.jwt = data.jwt
            return
        raise ValueError("必须提供jwt或appId和appSecret")

    async def keep_alive(self):
        try:
            jwt_data = self.decode_jwt(self.base_info.jwt)[1]
            if (jwt_data.exp.timestamp() - time()) < 3600:
                await self.login()
            log.debug(f"{self} | keep alive")
            await sleep(60)
        except Exception as e:
            log.debug(f"{self} | keep alive failed: <r>{e}</r>")

    @_with_update_info
    async def updateNickname(self, nickname: str):
        """更新昵称，机器人重登后就失效了"""
        return await self.updateUserField(fieldName="nickname", fieldValue=nickname)

    @_with_update_info
    async def updateAvatar(self, avatar: str):
        """更新头像，机器人重登后就失效了"""
        return await self.updateUserField(fieldName="avatar", fieldValue=avatar)

    async def upload(self, *, file: bytes) -> FileInfo:
        """上传文件"""
        return TypeAdapter(FileInfo).validate_python(
            await self.call_api(
                "upload",
                kvs_={
                    "files": {"file": file},
                },
                use_api_=False,
                use_http_=True,
                use_sio_=False,
                raw_data_=True,
            )
        )
