from nonebot.rule import Rule

from .event import Event


async def _not_self(event: Event) -> bool:
    return not event.is_self()


"""不是机器人自己的事件"""
NotSelf: Rule = Rule(_not_self)
