from nonebot.internal.permission import Permission

from nonebot_adapter_tailchat.event import DefaultMessageEvent


async def _private(event: DefaultMessageEvent) -> bool:
    return not event.is_group()


async def _group(event: DefaultMessageEvent) -> bool:
    return event.is_group()


GROUP: Permission = Permission(_group)

PRIVATE: Permission = Permission(_private)
