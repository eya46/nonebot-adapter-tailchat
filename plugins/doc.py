from nonebot import on_command

from nonebot_adapter_tailchat import MessageSegment
from nonebot_adapter_tailchat.rule import NotSelf

doc = on_command("doc", rule=NotSelf)


@doc.handle()
async def handle_echo():
    await doc.send(
        MessageSegment.url(url="https://tailchat.msgbyte.com/zh-Hans/docs/intro", text="点击查看文档")
        + MessageSegment.emoji("laughing")
    )
