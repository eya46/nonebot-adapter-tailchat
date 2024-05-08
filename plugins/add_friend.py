from nonebot import on_command
from nonebot.params import CommandArg
from nonebot.permission import SUPERUSER

from nonebot_adapter_tailchat import Bot, Message
from nonebot_adapter_tailchat.exception import ActionFailed

add_friend = on_command("add_friend", permission=SUPERUSER)


@add_friend.handle()
async def add_friend_handle(bot: Bot, cmd: Message = CommandArg()):
    arg = cmd.extract_plain_text().strip()
    try:
        await bot.addRequest(to=arg, message="求求你了，加我好友吧！让我做什么都可以~")
    except ActionFailed as e:
        await add_friend.finish(f"add friend {arg} fail: {e.message}")
    except Exception as e:
        await add_friend.finish(f"add friend {arg} fail: {e}")

    await add_friend.finish(f"add friend {arg}")
