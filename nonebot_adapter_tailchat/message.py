from abc import ABC
from collections import UserDict, defaultdict, deque
from collections.abc import Iterable
from dataclasses import dataclass
from functools import wraps
from typing import Optional, TypedDict, TypeVar, Union

from nonebot.adapters import (
    Message as BaseMessage,
)
from nonebot.adapters import (
    MessageSegment as BaseMessageSegment,
)
from typing_extensions import Self, override

from .bbcode import Parser

B = TypeVar("B", bound="BBCode")
TEXTS: set[str] = set()
BBCODES: dict[str, type[B]] = {}
RELATION: dict[int, list[B]] = defaultdict(list)


def _register_text(bbcode: type[B]) -> type[B]:
    TEXTS.update(bbcode.tags)
    return bbcode


def _register_bbcode(code: Union[int, type[B]]):
    if isinstance(code, int):

        def _(bbcode: type[B]) -> type[B]:
            bbcode.relation = code
            for tag in bbcode.tags:
                BBCODES[tag] = bbcode
            RELATION[code].append(bbcode)
            return bbcode

        return _
    for tag in code.tags:
        BBCODES[tag] = code
    _code = min(min(RELATION.keys() or [0]), 0) - 1
    code.relation = _code
    RELATION[_code].append(code)
    return code


class Box(TypedDict):
    text: str
    extra: dict[str, str]
    tags: list[B]


class BBCode(UserDict, ABC):
    relation: int
    keys_: set[str] = set()
    tags: set[str]

    def __init__(self, *, box: Box):
        self.data: dict[str, str]  # 标签内的kv
        super().__init__(box["extra"])
        self.box = box
        for _ in self.tags:
            self.tag = _
        self.main: Optional[str] = None  # [tag=value]text[/tag]的value
        for _ in self.tags:
            self.main = self.main or self.get(_)

    @property
    def text(self) -> str:
        return self.box["text"]

    @property
    def head(self) -> str:
        return (
            "["
            + (
                (f"{self.tag}={self.main} " if self.main else self.tag)
                + " ".join(f"{k}={v}" for k, v in self.items() if k in self.keys_ and k not in self.tags)
            ).rstrip(" ")
            + "]"
        )

    @property
    def tail(self) -> str:
        return f"[/{self.tag}]"

    @classmethod
    def tag_in(cls, msg: Union["MessageSegment", "Message"]) -> bool:
        if isinstance(msg, MessageSegment):
            return any(type(_) is cls for _ in msg.data["tags"])

        return any(BBCode.tag_in(_) for _ in msg)

    def __str__(self):
        return self.head + self.text + self.tail

    def __repr__(self):
        return f"{self.tag}({self.data})" if len(self.data) else f"{self.tag}"


@_register_bbcode
class Markdown(BBCode):
    tags = {"md", "markdown"}


@_register_bbcode
class Card(BBCode):
    tags = {"card"}
    keys_ = {"type", "data"}

    @property
    def type(self) -> str:
        return self["type"]

    @property
    def card_data(self) -> str:
        return self["data"]


@_register_bbcode
class File(BBCode):
    tags = {"file"}
    keys_ = {"url"}

    @property
    def url(self) -> str:
        return self["url"]


@_register_bbcode
class Emoji(BBCode):
    tags = {"emoji"}


@_register_text
@_register_bbcode(0)
class Bold(BBCode):
    tags = {"b"}


@_register_text
@_register_bbcode(0)
class Italic(BBCode):
    tags = {"i"}


@_register_text
@_register_bbcode(0)
class Underline(BBCode):
    tags = {"u"}


@_register_text
@_register_bbcode(0)
class Strikeout(BBCode):
    tags = {"s"}


@_register_bbcode
class At(BBCode):
    tags = {"at"}
    keys_ = {"at"}

    @property
    def uid(self) -> str:
        return self.main


@_register_bbcode
class Url(BBCode):
    tags = {"url"}
    keys_ = {"url"}

    @property
    def url(self) -> str:
        return self["url"]


@dataclass
class MessageSegment(BaseMessageSegment["Message"]):
    data: Box

    @classmethod
    @override
    def get_message_class(cls) -> type["Message"]:
        return Message

    @override
    def __str__(self) -> str:
        return self.data["text"]

    def get_text(self) -> str:
        return self.data["text"]

    @override
    def is_text(self) -> bool:
        return not any(not (_.tags & TEXTS) for _ in self.data["tags"])

    @classmethod
    def card(cls, *, text: str, type_: str, data: str) -> "MessageSegment":
        return cls.build(text, [Card], {"type": type_, "data": data})

    @classmethod
    def at(cls, *, uid: str, nickname: Optional[str] = None) -> "MessageSegment":
        return cls.build(nickname or uid, [At], {"at": uid})

    @classmethod
    def file(cls, *, name: str, url: str) -> "MessageSegment":
        return cls.build(name, [File], {"url": url})

    @classmethod
    def url(cls, *, url: str, text: Optional[str] = None) -> Self:
        return cls.build(text or url, [Url], {"url": url})

    @classmethod
    def text(cls, text: str, *, b: bool = False, i: bool = False, u: bool = False, s: bool = False) -> Self:
        _: list[type[B]] = []
        if b:
            _.append(Bold)
        if i:
            _.append(Italic)
        if u:
            _.append(Underline)
        if s:
            _.append(Strikeout)
        return cls.build(text, _)

    @classmethod
    def emoji(cls, text: str) -> Self:
        return cls.build(text, [Emoji])

    @classmethod
    def build(cls, text: str, tags: list[type[B]], extra: Optional[dict[str, str]] = None) -> Self:
        if extra is None:
            extra = {}
        _ = cls("text", {"text": text, "extra": extra, "tags": []})
        for tag in tags:
            _.data["tags"].append(tag(box=_.data))
        return _

    def tag_relation(self) -> set[int]:
        return {_.relation for _ in self.data["tags"]}

    def extend(self, seg: "MessageSegment", strict: bool = True) -> Self:
        if strict and (relations := self.tag_relation()) and any(_.relation not in relations for _ in seg.data["tags"]):
            raise ValueError("Tag relation not match")
        self.data["extra"].update(seg.data["extra"])
        for idx, tag in enumerate(seg.data["tags"]):
            seg.data["tags"][idx] = tag.__class__(box=self.data)
        self.data["tags"].extend(seg.data["tags"])
        return self

    def remove(self, bbcode: Union[B, type[B]]) -> Self:
        if bbcode is type[B]:
            bbcode: B = self.get_tag(bbcode)
        self.data["tags"].remove(bbcode)
        for _ in bbcode.keys_ | bbcode.tags:
            self.data["extra"].pop(_, _)

        return self

    def down(self, bbcode: Union[B, type[B]]) -> Self:
        """把bbcode变为文本"""
        if bbcode is type[B]:
            bbcode: B = self.get_tag(bbcode)
        self.data["text"] = str(bbcode)
        return self.remove(bbcode)

    def get_tag(self, bbcode: type[B]) -> Optional[B]:
        for _ in self.data["tags"]:
            if _ is bbcode:
                return _
        return None

    def decode(self) -> str:
        _ = deque([self.data["text"]])
        for tag in self.data["tags"]:
            _.appendleft(tag.head)
            _.append(tag.tail)
        return "".join(_)


def _update_parser(func):
    @wraps(func)
    def _(*args, **kwargs):
        res = func(*args, **kwargs)
        Message.parser = Parser(MessageSegment, BBCODES)
        return res

    return _


class Message(BaseMessage[MessageSegment]):
    parser: Parser = Parser(MessageSegment, BBCODES)

    @classmethod
    def update_parser(cls):
        cls.parser = Parser(MessageSegment, BBCODES)

    @staticmethod
    def register_bbcode(code: Union[int, type[B]]):
        return _register_bbcode(code)

    @staticmethod
    def register_text(bbcode: type[B]) -> type[B]:
        """注册文本类型"""
        return _register_text(bbcode)

    def __contains__(  # pyright: ignore[reportIncompatibleMethodOverride]
        self, value: Union[MessageSegment, str, B, type[B]]
    ) -> bool:
        """检查消息段是否存在

        参数:
            value: 消息段或消息段类型
        返回:
            消息内是否存在给定消息段或给定类型的消息段
        """
        if value is type[B]:
            return value.tag_in(self)
        return super().__contains__(value)

    @classmethod
    @override
    def get_segment_class(cls) -> type[MessageSegment]:
        return MessageSegment

    @classmethod
    @override
    def _construct(cls, msg: str) -> Iterable[MessageSegment]:
        yield from cls.parser.tokenize(msg)

    @override
    def extract_plain_text(self) -> str:
        return "".join(seg.data["text"] for seg in self if seg.is_text())

    def decode(self) -> str:
        return "".join(seg.decode() for seg in self)
