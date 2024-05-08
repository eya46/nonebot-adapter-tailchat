from datetime import datetime as raw_datetime
from typing import Annotated, Optional

from pydantic import BaseModel, BeforeValidator, ByteSize, ConfigDict, Field, RootModel

from .config import BotInfo
from .message import Message, MessageSegment
from .util import unpack

datetime = Annotated[
    raw_datetime,
    BeforeValidator(unpack),
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

    parentId: Optional[int] = None
    pluginPanelName: Optional[int] = None
    provider: Optional[int] = None


class Replay(RawModel):
    id: str = Field(alias="_id")
    content: str
    author: str


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
    mentions: list[str]

    replay: Optional[Replay] = None


class Payload(RawModel):
    converseId: str
    messageId: str
    messageAuthor: str
    messageSnippet: Message
    messagePlainContent: Message

    groupId: Optional[str] = None


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
    _id: str
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
    _id: str
    type: str
    members: list[str]
    createdAt: datetime
    updatedAt: datetime

    v: int = Field(alias="__v")


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
    _id: str
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


class GroupInfo(RawModel):
    _id: str
    name: str
    owner: str
    members: list[MemberInfo]
    panels: list[Panel]
    roles: list[str]
    fallbackPermissions: list[str]
    createdAt: datetime
    updatedAt: datetime

    v: int = Field(alias="__v")

    config: Optional[dict] = None
    description: Optional[int] = None
    avatar: Optional[int] = None


class AddFriendRequestRet(RawModel):
    id: str = Field(alias="_id")  # requestId
    from_: str = Field(alias="from")
    to: str = Field(alias="to")
    v: int = Field(alias="__v")


class GroupAndPanelIds(RawModel):
    groupIds: list[str]
    textPanelIds: list[str]
    subscribeFeaturePanelIds: list[str]
