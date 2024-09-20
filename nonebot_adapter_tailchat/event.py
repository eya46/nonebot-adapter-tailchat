from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Literal, Optional, TypeVar, Union, cast, get_args

from nonebot.adapters import Event as BaseEvent
from nonebot.compat import model_dump
from pydantic import Field
from pydantic_core import PydanticUndefined
from typing_extensions import Self

from .message import At, Message, MessageSegment
from .model import (
    Announcement,
    ConverseType,
    GroupInfo,
    MessageMeta,
    MessageRet,
    ObjectId,
    Payload,
    Reaction,
    Reply,
    StaticAnnouncement,
    datetime,
)
from .util import log

if TYPE_CHECKING:
    from .bot import Bot


class Event(BaseEvent, ABC):
    event_name: str
    event_type: str

    self_id: ObjectId

    _isToMe: bool = False

    def get_type(self) -> str:
        return self.event_type

    def get_event_name(self) -> str:
        return self.event_name

    def get_event_description(self) -> str:
        return str(model_dump(self))

    def is_tome(self) -> bool:
        return not self.is_self() and (self._isToMe or self._is_tome)

    @property
    @abstractmethod
    def _is_tome(self) -> bool:
        return True

    def is_self(self) -> bool:
        return self.self_id == self.get_user_id()

    async def _get_message(self, bot: "Bot" = None) -> Message:
        return self.get_message()

    @classmethod
    async def build(cls, bot: "Bot", obj: dict) -> Self:
        event = cls.model_validate(obj)
        try:
            message: Message = await event._get_message(bot)
            # at
            seg: MessageSegment = message[0]
            if seg.type == At.__name__.lower():
                if seg.get_tag(At).main == event.self_id:
                    event._isToMe = True
                    message.pop(0)
            # nickname
            elif seg.type == "text":
                text = seg.get_text().strip()
                for i in bot.config.nickname:
                    if text.startswith(i):
                        event._isToMe = True
                        if len(text) == len(i):
                            message.pop(0)
                        else:
                            seg.data["text"] = text[len(i) :]
        except Exception as e:
            log.debug(f"Event.build error: {e}")
        return event


class NoticeEvent(Event, ABC):
    event_type: Literal["notice"] = "notice"

    def get_session_id(self) -> str:
        raise NotImplementedError

    def get_message(self) -> Message:
        raise NotImplementedError


class RequestEvent(Event, ABC):
    event_type: Literal["request"] = "request"

    def get_session_id(self) -> str:
        raise ValueError("Event has no context!")

    def get_message(self) -> Message:
        raise ValueError("Event has no context!")


class MessageEvent(Event, ABC):
    event_type: Literal["message"] = "message"

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
        return (
            f"{self.get_group_id()}:{self.get_converse_id()}:{self.get_user_id()}"
            if self.is_group()
            else f"{self.get_converse_id()}:{self.get_user_id()}"
        )


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
            if not isinstance(self.content, Message):
                setattr(self, "content", Message(self.content))
            return self.content
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


def remove_event_class(event_class: type[E]) -> type[E]:
    if event_class.model_fields["event_type"].default == PydanticUndefined:
        return event_class
    try:
        event_name = getattr(event_class, "event_name", get_args(event_class.__annotations__["event_name"])[0])
        EVENT_CLASSES.pop(event_name, None)
        return event_class
    except:
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
        return True

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

    groupId: ObjectId

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


class DefaultReactionEvent(NoticeEvent):
    converseId: ObjectId
    messageId: ObjectId
    reaction: Reaction

    message: Optional[MessageRet] = None
    content: Optional[Message] = None

    def get_user_id(self) -> str:
        return self.reaction.author

    @property
    def _is_tome(self) -> bool:
        if self.message:
            return self.message.author == self.self_id
        return False

    def get_session_id(self) -> str:
        return f"{self.converseId}:{self.messageId}:{self.reaction.author}"

    def is_group(self) -> bool:
        if self.message is None:
            raise ValueError("Event has no context!")
        return not not self.message.groupId

    def get_message(self) -> Message:
        if self.content:
            return self.content
        return super().get_message()

    async def _get_message(self, bot: Optional["Bot"] = None) -> Message:
        if self.content:
            return self.content
        if self.message:
            self.content = Message(self.message.content)
            return self.content
        if bot:
            self.message = await bot.getMessage(messageId=self.messageId)
            self.content = Message(self.message.content)
            return self.content
        raise ValueError("Event has no context!")


@register_event_class
class DefaultReactionAddEvent(DefaultReactionEvent):
    event_name: Literal["notify:chat.message.addReaction"]

    @classmethod
    async def build(cls, bot: "Bot", obj: dict) -> Self:
        event = cast(cls, await super().build(bot, obj))
        if event.message is None:
            return event
        if event.is_group():
            return GroupReactionAddEvent.model_validate(dict(event))
        return PrivateReactionAddEvent.model_validate(dict(event))


class PrivateReactionAddEvent(DefaultReactionAddEvent):
    message: MessageRet
    content: Message

    def is_group(self) -> bool:
        return False


class GroupReactionAddEvent(DefaultReactionAddEvent):
    message: MessageRet
    content: Message

    def is_group(self) -> bool:
        return True

    @property
    def groupId(self) -> ObjectId:
        return self.message.groupId


@register_event_class
class DefaultReactionRemoveEvent(DefaultReactionEvent):
    event_name: Literal["notify:chat.message.removeReaction"]

    @classmethod
    async def build(cls, bot: "Bot", obj: dict) -> Self:
        event = cast(cls, await super().build(bot, obj))
        if event.message is None:
            return event
        if event.is_group():
            return GroupReactionRemoveEvent.model_validate(dict(event))
        return PrivateReactionRemoveEvent.model_validate(dict(event))


class PrivateReactionRemoveEvent(DefaultReactionRemoveEvent):
    message: MessageRet
    content: Message

    def is_group(self) -> bool:
        return False


class GroupReactionRemoveEvent(DefaultReactionRemoveEvent):
    message: MessageRet
    content: Message

    def is_group(self) -> bool:
        return True

    @property
    def groupId(self) -> ObjectId:
        return self.message.groupId


class DefaultMessageEvent(MessageEvent):
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

    groupId: Optional[ObjectId] = Field(default=None)

    def get_message_id(self) -> str:
        return self.id

    def get_converse_id(self) -> str:
        return self.converseId

    def get_group_id(self) -> Optional[str]:
        return self.groupId

    @property
    def reply(self) -> Optional[Reply]:
        return self.meta.reply if self.meta else None

    def get_message(self) -> Message:
        return self.content

    def get_user_id(self) -> str:
        return self.author

    def _is_tome(self) -> bool:
        # 私聊/提及/回复
        return (
            not self.is_group()
            or (self.meta and self.self_id in self.meta.mentions)
            or (self.meta and self.meta.reply and self.self_id == self.meta.reply.author)
        )

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


class AtEvent(Event, ABC): ...


@register_event_class
class AtMessageEvent(MessageEvent, AtEvent):
    event_name: Literal["notify:chat.inbox.append"]

    type: str

    v: int = Field(alias="__v")

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

    def get_user_id(self) -> str:
        return self.payload.messageAuthor

    def get_event_description(self) -> str:
        return (
            f"AtMessage {self.payload.messageId} from {self.payload.messageAuthor}"
            + (f"@[群:{self.get_group_id()}]" if self.payload.groupId else "")
            + f" {self.payload.messageSnippet.show()}"
        )


@register_event_class
class AtMessageUpdateEvent(NoticeEvent, AtEvent):
    """At 消息更新事件
    (目前只有@Bot消息删除会触发)"""

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
