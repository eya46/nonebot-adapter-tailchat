from nonebot import on_command
from nonebot.params import CommandArg
from nonebot.permission import SUPERUSER

from nonebot_adapter_tailchat import Bot, Message

add_group = on_command("add_group", permission=SUPERUSER)


@add_group.handle()
async def add_group_handle(bot: Bot, cmd: Message = CommandArg()):
    arg = cmd.extract_plain_text().strip()
    code_info = await bot.findInviteByCode(code=arg)
    if code_info is None:
        await add_group.finish(f"No such invite code")
    if await bot.isMember(groupId=code_info.groupId):
        await add_group.finish(f"Already in group {code_info.groupId}")
    await bot.applyInvite(code=arg)
    await add_group.finish(f"Applied invite code {arg}")
