from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Literal, Optional, TypeVar, Union, get_args

from nonebot.adapters import Event as BaseEvent
from nonebot.compat import model_dump
from pydantic import Field
from pydantic_core import PydanticUndefined
from typing_extensions import override

from .message import Message
from .model import (
    Announcement,
    ConverseType,
    GroupInfo,
    MessageMeta,
    ObjectId,
    Payload,
    Reaction,
    Replay,
    StaticAnnouncement,
    datetime,
)

if TYPE_CHECKING:
    from .bot import Bot


class Event(BaseEvent, ABC):
    event_name: str
    event_type: str

    self_id: ObjectId

    @override
    def get_type(self) -> str:
        return self.event_type

    @override
    def get_event_name(self) -> str:
        return self.event_name

    @override
    def get_event_description(self) -> str:
        return str(model_dump(self))

    @override
    def is_tome(self) -> bool:
        return not self.is_self() and self._is_tome

    @property
    @abstractmethod
    def _is_tome(self) -> bool:
        return True

    def is_self(self) -> bool:
        return self.self_id == self.get_user_id()


class NoticeEvent(Event, ABC):
    event_type: Literal["notice"] = "notice"

    def get_message(self) -> Message:
        raise ValueError("Event has no message!")

    def get_session_id(self) -> str:
        raise ValueError("Event has no context!")


class RequestEvent(Event, ABC):
    event_type: Literal["request"] = "request"

    @override
    def get_session_id(self) -> str:
        raise ValueError("Event has no context!")

    @override
    def get_message(self) -> Message:
        raise ValueError("Event has no context!")


class MessageEvent(Event, ABC):
    event_type: Literal["message"] = "message"

    @override
    def get_plaintext(self) -> str:
        return self.get_message().extract_plain_text()

    @abstractmethod
    def get_message_id(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def get_converse_id(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def is_group(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def get_group_id(self) -> Optional[str]:
        raise NotImplementedError

    def get_session_id(self) -> str:
        return f"{self.get_group_id()}:{self.get_converse_id()}" if self.is_group() else self.get_converse_id()


class UnknownEvent(Event):
    event_type: Literal["unknown"] = "unknown"

    @property
    def _is_tome(self) -> bool:
        return False

    def get_user_id(self) -> str:
        raise ValueError("Unknown event has no context!")

    def get_session_id(self) -> str:
        raise ValueError("Unknown event has no context!")

    def get_message(self) -> "Message":
        if hasattr(self, "content"):
            return Message(self.content)
        raise ValueError("Unknown event has no message content")


EVENT_CLASSES: dict[str, type[Event]] = {}

E = TypeVar("E", bound=Event)


def get_event(event_name: str) -> type[Event]:
    return EVENT_CLASSES.get(event_name, UnknownEvent)


def register_event_class(event_class: type[E]) -> type[E]:
    if event_class.model_fields["event_type"].default == PydanticUndefined:
        raise ValueError(f"Event class {event_class} must have a field `event_type`")
    try:
        event_name = getattr(event_class, "event_name", get_args(event_class.__annotations__["event_name"])[0])
    except Exception as e:
        raise ValueError(
            f"Event class {event_class} must have a default value or Literal[str] type annotation for `event_name`"
        ) from e  # event_name 必须 有默认值 或 Literal[str] 类型注解
    EVENT_CLASSES[event_name] = event_class
    return event_class


@register_event_class
class ClientConfigUpdateEvent(NoticeEvent):
    event_name: Literal["notify:config.updateClientConfig"]

    serverName: str
    serverEntryImage: str
    announcement: Union[StaticAnnouncement, Literal[False]]

    @property
    def _is_tome(self) -> bool:
        return True

    def get_user_id(self) -> str:
        return "000000000000000000000000"


@register_event_class
class DMConverseUpdateEvent(NoticeEvent):
    """创建私信会话时的事件"""

    event_name: Literal["notify:chat.converse.updateDMConverse"]

    id: ObjectId = Field(alias="_id")  # 应该是converseId
    type: ConverseType  # DM, Multi
    members: list[ObjectId]
    createdAt: datetime
    updatedAt: datetime

    v: int = Field(alias="__v")

    @property
    def _is_tome(self) -> bool:
        # TODO: 判断是否是自己
        return False

    def get_user_id(self) -> str:
        raise ValueError("Event has no context!")


@register_event_class
class MessageDeleteEvent(NoticeEvent):
    event_name: Literal["notify:chat.message.delete"]

    converseId: ObjectId
    messageId: ObjectId

    @property
    def _is_tome(self) -> bool:
        # TODO: 提供信息过少
        return False

    def get_user_id(self) -> str:
        # TODO: 提供信息过少
        raise ValueError("Event has no context!")


class GroupInfoEvent(NoticeEvent, ABC):
    @property
    def _is_tome(self) -> bool:
        # TODO: 不好判断
        return False


@register_event_class
class AddGroupEvent(GroupInfoEvent, GroupInfo):
    """机器人加群事件"""

    event_name: Literal["notify:group.add"]

    @property
    def _is_tome(self) -> bool:
        return True

    def get_user_id(self) -> str:
        return self.self_id


@register_event_class
class RemoveGroupEvent(GroupInfoEvent):
    """机器人退群事件"""

    event_name: Literal["notify:group.remove"]

    groupId: str

    @property
    def _is_tome(self) -> bool:
        return True

    def get_user_id(self) -> str:
        return self.self_id


@register_event_class
class GroupInfoUpdateEvent(GroupInfoEvent, GroupInfo):
    """群信息更新/用户加群事件"""

    event_name: Literal["notify:group.updateInfo"]

    def get_user_id(self) -> str:
        # TODO: ...
        raise ValueError("Event has no context!")


class ReactionEvent(NoticeEvent):
    converseId: ObjectId
    messageId: ObjectId
    reaction: Reaction

    def get_user_id(self) -> str:
        return self.reaction.author

    @property
    def _is_tome(self) -> bool:
        # TODO: ...
        return False

    def get_session_id(self) -> str:
        return f"{self.converseId}:{self.messageId}:{self.reaction.author}"


@register_event_class
class ReactionAddEvent(ReactionEvent):
    event_name: Literal["notify:chat.message.addReaction"]


@register_event_class
class ReactionRemoveEvent(ReactionEvent):
    event_name: Literal["notify:chat.message.removeReaction"]


class DefaultMessageEvent(MessageEvent):
    def get_message_id(self) -> str:
        return self.id

    def get_converse_id(self) -> str:
        return self.converseId

    def get_group_id(self) -> Optional[str]:
        return self.groupId

    id: ObjectId = Field(alias="_id")
    author: ObjectId
    hasRecall: bool
    converseId: ObjectId
    meta: Optional[MessageMeta] = Field(default=None)

    content: Message
    raw_content: str = Field(alias="content")
    reactions: list[Reaction]
    createdAt: datetime
    updatedAt: datetime

    groupId: Optional[str] = Field(default=None)

    @property
    def replay(self) -> Optional[Replay]:
        return self.meta.replay if self.meta else None

    @override
    def get_message(self) -> Message:
        return self.content

    @override
    def get_user_id(self) -> str:
        return self.author

    def _is_tome(self) -> bool:
        return not self.is_group() or (self.meta and self.self_id in self.meta.mentions)

    @override
    def get_event_description(self) -> str:
        return (
            f"Message {self.id} from {self.author}"
            + (f"@[群:{self.groupId}]" if self.groupId else "")
            + f" {self.content.show()}"
        )

    def is_group(self) -> bool:
        return not not self.groupId


@register_event_class
class MessageAddEvent(DefaultMessageEvent):
    event_name: Literal["notify:chat.message.add"]


@register_event_class
class MessageUpdateEvent(DefaultMessageEvent):
    """消息更新事件(撤回消息)"""

    event_name: Literal["notify:chat.message.update"]


class AtEvent(Event, ABC):
    event_type: Literal["message"] = "message"

    type: str

    v: int = Field(alias="__v")


@register_event_class
class AtMessageEvent(AtEvent, MessageEvent):
    event_name: Literal["notify:chat.inbox.append"]

    id: ObjectId = Field(alias="_id")
    userId: ObjectId
    payload: Union[Payload, Announcement]
    readed: bool
    createdAt: datetime
    updatedAt: datetime

    def get_message(self) -> Message:
        return self.payload.messageSnippet

    def get_message_id(self) -> str:
        return self.payload.messageId

    def get_converse_id(self) -> str:
        return self.payload.converseId

    def get_group_id(self) -> Optional[str]:
        return self.payload.groupId

    def is_group(self):
        return not not self.payload.groupId

    def _is_tome(self) -> bool:
        return True

    @override
    def get_user_id(self) -> str:
        return self.payload.messageAuthor

    @override
    def get_event_description(self) -> str:
        return (
            f"AtMessage {self.payload.messageId} from {self.payload.messageAuthor}"
            + (f"@[群:{self.get_group_id()}]" if self.payload.groupId else "")
            + f" {self.payload.messageSnippet.show()}"
        )


@register_event_class
class AtMessageUpdateEvent(AtEvent, NoticeEvent):
    """At 消息更新事件"""

    event_name: Literal["notify:chat.inbox.updated"]

    @property
    def _is_tome(self) -> bool:
        return True

    def get_user_id(self) -> str:
        raise ValueError("Event has no context!")


@register_event_class
class FriendRequestAddEvent(RequestEvent):
    event_name: Literal["notify:friend.request.add"]

    id: ObjectId = Field(alias="_id")
    from_: ObjectId = Field(alias="from")
    to: ObjectId
    v: int = Field(alias="__v")

    async def accept(self, bot: "Bot"):
        return await bot.acceptRequest(requestId=self.id)

    async def deny(self, bot: "Bot"):
        return await bot.denyRequest(requestId=self.id)

    @property
    def _is_tome(self) -> bool:
        return True

    def get_user_id(self) -> str:
        return self.from_


@register_event_class
class FriendRequestRemoveEvent(RequestEvent):
    event_name: Literal["notify:friend.request.remove"]

    requestId: ObjectId

    @property
    def _is_tome(self) -> bool:
        return True

    def get_user_id(self) -> str:
        # TODO: 提供信息过少
        raise ValueError("Event has no context!")
