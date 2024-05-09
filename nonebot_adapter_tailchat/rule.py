from nonebot.rule import Rule

from .event import Event, ReactionEvent


async def _not_self(event: Event) -> bool:
    return not event.is_self()


"""不是机器人自己的事件"""
NotSelf: Rule = Rule(_not_self)


def targetMessageReactionEvent(messageId: str) -> Rule:
    """指定消息的 ReactionEvent"""

    async def _target_message(event: ReactionEvent) -> bool:
        return event.messageId == messageId

    return Rule(_target_message)
