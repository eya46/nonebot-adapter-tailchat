from abc import ABC, abstractmethod
from typing import Literal, Optional, TypeVar, get_args

from nonebot.adapters import Event as BaseEvent
from nonebot.compat import model_dump
from pydantic import Field
from typing_extensions import override

from .message import Message
from .model import MemberInfo, MessageMeta, Panel, Payload, Reaction, Replay, datetime


class Event(BaseEvent):
    event_name: str
    event_type: str = Field(alias="event_name")
    self_id: str

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
    def get_session_id(self) -> str:
        raise ValueError("Event has no context!")

    def get_user_id(self) -> str:
        raise ValueError("Event has no context!")

    def get_message(self) -> "Message":
        raise ValueError("Event has no message!")

    @override
    def is_tome(self) -> bool:
        return not self.is_self() and self._is_tome()

    @staticmethod
    def _is_tome() -> bool:
        return True

    def is_self(self) -> bool:
        return self.self_id == self.get_user_id()


EVENT_CLASSES: dict[str, type[Event]] = {}

E = TypeVar("E", bound=Event)


def register_event_class(event_class: type[E]) -> type[E]:
    try:
        event_name = getattr(event_class, "event_name", get_args(event_class.__annotations__["event_name"])[0])
    except Exception as e:
        raise ValueError(
            f"Event class {event_class} must have a default value or Literal[str] type annotation for `event_name`"
        ) from e  # event_name 必须 有默认值 或 Literal[str] 类型注解
    EVENT_CLASSES[event_name] = event_class
    return event_class


@register_event_class
class MessageDeleteEvent(Event):
    event_name: Literal["notify:chat.message.delete"] = "notify:chat.message.delete"

    converseId: str
    messageId: str


class GroupInfoEvent(Event):
    id: str = Field(alias="_id")
    name: str
    owner: str
    members: list[MemberInfo]
    panels: list[Panel]
    roles: list[str]
    fallbackPermissions: list[str]
    createdAt: datetime
    updatedAt: datetime
    __v: int

    config: Optional[dict] = None
    description: Optional[int] = None
    avatar: Optional[int] = None


@register_event_class
class GroupInfoUpdateEvent(GroupInfoEvent):
    event_name: Literal["notify:group.updateInfo"]


class ReactionEvent(Event):
    converseId: str
    messageId: str
    reaction: Reaction


@register_event_class
class ReactionAddEvent(ReactionEvent):
    event_name: Literal["notify:chat.message.addReaction"]


@register_event_class
class ReactionRemoveEvent(ReactionEvent):
    event_name: Literal["notify:chat.message.addReaction"]


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


class DefaultMessageEvent(MessageEvent):
    def get_message_id(self) -> str:
        return self.id

    def get_converse_id(self) -> str:
        return self.converseId

    def get_group_id(self) -> Optional[str]:
        return self.groupId

    id: str = Field(alias="_id")
    author: str
    hasRecall: bool
    converseId: str
    meta: Optional[MessageMeta] = Field(default=None)

    content: Message
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

    @override
    def get_session_id(self) -> str:
        return self.converseId

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


class AtEvent(Event):
    type: str

    v: int = Field(alias="__v")


@register_event_class
class AtMessageEvent(AtEvent, MessageEvent):
    event_name: Literal["notify:chat.inbox.append"]

    id: str = Field(alias="_id")
    userId: str
    payload: Payload
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
class MessageAddEvent(DefaultMessageEvent):
    event_name: Literal["notify:chat.message.add"]


@register_event_class
class MessageUpdateEvent(DefaultMessageEvent):
    event_name: Literal["notify:chat.message.update"]
