from nonebot import on_command

from nonebot_adapter_tailchat import Bot
from nonebot_adapter_tailchat.event import MessageEvent
from nonebot_adapter_tailchat.rule import NotSelf

ping = on_command("ping", rule=NotSelf)


@ping.handle()
async def handle_echo(bot: Bot, event: MessageEvent):
    await bot.addReaction(emoji=":smirk:", messageId=event.get_message_id())
    await ping.send("pong")
