from asyncio import Task, create_task, sleep
from typing import Optional

from nonebot import get_bots, get_driver, get_plugin_config, logger
from pydantic import BaseModel, Field

from nonebot_adapter_tailchat import Bot


class Config(BaseModel):
    invite_codes: list[str] = Field(default_factory=list)


config = get_plugin_config(Config)

task: Optional[Task] = None

driver = get_driver()


@driver.on_startup
async def _():
    global task
    task = create_task(auto_add_group())


@driver.on_shutdown
async def _():
    global task
    if task:
        task.cancel()


async def auto_add_group():
    logger.info("will auto add group after 10 seconds")
    await sleep(10)
    bots = get_bots().values()
    for bot in bots:
        if isinstance(bot, Bot):
            bot: Bot
            for invite_code in config.invite_codes:
                code_info = await bot.findInviteByCode(code=invite_code)
                if code_info is None:
                    logger.info(f"{bot}: No such invite code")
                    continue
                if await bot.isMember(groupId=code_info.groupId):
                    logger.info(f"{bot}: Already in group {code_info.groupId}")
                    continue
                await bot.applyInvite(code=invite_code)
                logger.info(f"{bot}: Applied invite code {invite_code}")
