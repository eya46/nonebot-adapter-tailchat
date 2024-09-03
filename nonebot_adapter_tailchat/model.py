from collections import UserDict
from datetime import datetime as raw_datetime
from typing import Annotated, Literal, Optional, TypedDict

from pydantic import BaseModel, BeforeValidator, ByteSize, ConfigDict, Field, RootModel

from .config import BotInfo
from .message import Message, MessageSegment
from .util import unpack

datetime = Annotated[
    raw_datetime,
    BeforeValidator(unpack),
]

ObjectId = Annotated[str, Field(min_length=24, max_length=24)]
ConverseType = Literal[
    "DM",  # 私信
    "Multi",  # 多人
    "Group",  # 群组
]


class RawModel(BaseModel):
    model_config = ConfigDict(extra="allow")


class MemberInfo(RawModel):
    roles: list[str]
    userId: str

    muteUntil: Optional[datetime] = None


class Panel(RawModel):
    id: str
    name: str
    type: int
    fallbackPermissions: list[str]

    parentId: Optional[str] = None
    pluginPanelName: Optional[str] = None
    provider: Optional[str] = None


class Reply(RawModel):
    id: str = Field(alias="_id")
    content: Optional[str] = None
    author: Optional[str] = None


class Emoji(RootModel[str]):
    @property
    def name(self):
        return self.root[1:-1]

    def to_seg(self) -> MessageSegment:
        return MessageSegment.emoji(self.name)

    def __str__(self):
        return self.root


class Reaction(RawModel):
    name: Emoji
    author: str
    id: Optional[str] = Field(default=None, alias="_id")


class MessageMeta(RawModel):
    mentions: Optional[list[str]] = None

    reply: Optional[Reply] = None


class ReplyDict(TypedDict, total=False):
    _id: str
    content: Optional[str]
    author: Optional[str]


class MessageMetaDict(TypedDict, total=False):
    mentions: Optional[list[str]]
    reply: Optional[ReplyDict]


class Payload(RawModel):
    converseId: str
    messageId: str
    messageAuthor: str
    messageSnippet: Message
    messagePlainContent: Message

    groupId: Optional[str] = None


class Announcement(RawModel):
    title: str
    content: str  # md富文本


class StaticAnnouncement(RawModel):
    id: datetime
    text: str
    link: str


class ClientInfo(BotInfo):
    id: str = Field(alias="_id")
    login_time: datetime
    expire_time: datetime
    email: str
    userId: str
    nickname: str
    avatar: str


class BaseUserInfo(RawModel):
    userId: str = Field(alias="_id")
    nickname: str
    email: str

    avatar: Optional[str] = Field(default=None)


class BaseBotInfo(BaseUserInfo):
    jwt: str
    userId: str
    email: str
    nickname: str
    avatar: str  # bot avatar 默认为''


class JwtPayload(BaseUserInfo):
    avatar: str  # bot avatar 默认为''
    iat: datetime
    exp: datetime


class TokenInfo(RawModel):
    """token=jwt"""

    userId: str = Field(alias="_id")
    email: str
    nickname: str
    avatar: str
    temporary: bool
    type: str
    emailVerified: bool
    banned: bool
    createdAt: datetime
    token: str

    discriminator: Optional[str] = None


TemporaryUserInfo = TokenInfo


class MessageRet(RawModel):
    id: str = Field(alias="_id")
    content: str
    author: str
    converseId: str
    hasRecall: bool
    reactions: list[Reaction]
    createdAt: datetime
    updatedAt: datetime

    v: int = Field(alias="__v")

    groupId: Optional[str] = None
    meta: Optional[MessageMeta] = None


class ClientConfig(RawModel):
    uploadFileLimit: ByteSize
    emailVerification: bool
    disableUserRegister: bool
    disableGuestLogin: bool
    disableCreateGroup: bool
    disablePluginStore: bool
    disableAddFriend: bool
    disableTelemetry: bool
    serverName: str


class Ack(RawModel):
    userId: str
    converseId: str
    lastMessageId: str


class UserInfo(BaseUserInfo):
    temporary: bool  # 临时用户
    type: str
    emailVerified: bool
    banned: bool
    createdAt: datetime

    discriminator: Optional[str] = None  # eya46#1145 -> nickname#discriminator


class Whoami(RawModel):
    userAgent: str
    language: str
    user: BaseUserInfo
    token: str
    userId: str


class ConverseInfo(RawModel):
    id: str = Field(alias="_id")
    type: str
    members: list[str]
    createdAt: datetime
    updatedAt: datetime

    v: int = Field(alias="__v")

    name: Optional[str]


class LastMessages(RawModel):
    converseId: str
    lastMessageId: str


class Cpu(RawModel):
    load1: float
    load5: float
    load15: float
    cores: int
    utilization: int


class Memory(RawModel):
    free: ByteSize
    total: ByteSize
    percent: float


class ProcessMemory(RawModel):
    rss: ByteSize
    heapTotal: ByteSize
    heapUsed: ByteSize
    external: ByteSize
    arrayBuffers: ByteSize


class Process(RawModel):
    pid: int
    memory: ProcessMemory
    uptime: float
    argv: list[str]


class Health(RawModel):
    nodeID: str
    instanceID: str  # uuid
    cpu: Cpu
    memory: Memory
    process: Process
    services: list[str]
    version: str


class FileInfo(RawModel):
    etag: str
    path: str
    url: str


class InviteCodeInfo(RawModel):
    id: str = Field(alias="_id")
    code: str
    creator: str
    groupId: str
    usage: int
    createdAt: datetime
    updatedAt: datetime

    v: int = Field(alias="__v")


class BaseGroupInfo(RawModel):
    name: str
    owner: str
    description: str
    memberCount: int


class Role(RawModel):
    id: str = Field(alias="_id")
    name: str
    permissions: list[str]


class GroupInfo(RawModel):
    id: str = Field(alias="_id")
    name: str
    owner: str
    members: list[MemberInfo]
    panels: list[Panel]
    roles: list[Role]
    fallbackPermissions: list[str]
    createdAt: datetime
    updatedAt: datetime

    v: int = Field(alias="__v")

    config: Optional[dict] = None
    description: Optional[str] = None
    avatar: Optional[str] = None


class AddFriendRequestRet(RawModel):
    id: str = Field(alias="_id")  # requestId
    from_: str = Field(alias="from")
    to: str = Field(alias="to")
    v: int = Field(alias="__v")


class GroupAndPanelIds(RawModel):
    groupIds: list[str]
    textPanelIds: list[str]
    subscribeFeaturePanelIds: list[str]


class FindAndJoinRoomRet(RawModel):
    dmConverseIds: list[ObjectId]
    groupIds: list[ObjectId]
    textPanelIds: list[ObjectId]
    subscribeFeaturePanelIds: list[ObjectId]


class BotInfoRet(RawModel):
    id: ObjectId = Field(alias="_id")
    email: str
    nickname: str
    avatar: str


class GroupDataRet(UserDict):
    data: any
