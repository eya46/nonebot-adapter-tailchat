from abc import ABC
from collections import UserDict, defaultdict, deque
from collections.abc import Iterable
from dataclasses import dataclass
from functools import wraps
from inspect import isclass
from typing import Final, Optional, SupportsIndex, TypedDict, TypeVar, Union

from nonebot.adapters import (
    Message as BaseMessage,
)
from nonebot.adapters import (
    MessageSegment as BaseMessageSegment,
)
from typing_extensions import Self, overload

from .bbcode import Parser

BBCODE = TypeVar("BBCODE", bound="BBCode")
BBCODES: dict[str, Union[type[BBCODE], dict[str, BBCODE]]] = {}
RELATION: dict[int, list[BBCODE]] = defaultdict(list)


def _register_bbcode(code: Union[int, type[BBCODE]]):
    def _(bb: type[BBCODE]) -> type[BBCODE]:
        if bb.tags != {"card"}:
            for tag in bb.tags:
                BBCODES[tag] = bb
            return bb
        if (card := BBCODES.get("card")) is None:
            BBCODES["card"] = defaultdict(lambda: Card)  # type: ignore
        if bb.__name__ != "Card":
            card[bb.type] = bb

    if isinstance(code, int):

        def __(bbcode: type[BBCODE]) -> type[BBCODE]:
            bbcode.relation = code
            _(bbcode)
            RELATION[code].append(bbcode)
            return bbcode

        return __
    _(code)
    _code = min(min(RELATION.keys() or [0]), 0) - 1
    code.relation = _code
    RELATION[_code].append(code)
    return code


class Box(TypedDict):
    text: str
    extra: dict[str, str]
    tags: list[type[BBCODE]]


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

    def set_text(self, text: str):
        self.box["text"] = text

    @property
    def head(self) -> str:
        return (
            "["
            + (
                (f"{self.tag}={self.main}" if self.main else self.tag)
                + " "
                + " ".join(
                    f"{k}={v}" for k in sorted(self.keys_, reverse=True) if (v := self[k]) and k not in self.tags
                )
            ).rstrip(" ")
            + "]"
        )

    @property
    def tail(self) -> str:
        return f"[/{self.tag}]"

    @classmethod
    def tag_in(cls, msg: Union["MessageSegment", "Message"]) -> bool:
        if isinstance(msg, Message):
            for seg in msg:  # 递归
                if cls.tag_in(seg):
                    return True
            return False
        if cls == BBCode:  # 是BBCode
            return len(msg.tags) > 0
        elif isclass(cls):  # 子类
            return cls in msg.tags
        else:  # 实例化子类
            # 参数相同 + 在tags中
            return msg.extra | cls.data == msg.extra and type(cls) in msg.tags

    @classmethod
    def decode(cls, box: Box) -> str:
        return str(cls(box=box))

    def __str__(self):
        return self.head + self.text + self.tail

    def __repr__(self):
        return f"{self.tag}({self.data})" if len(self.data) else f"{self.tag}"

    def __missing__(self, key) -> None:
        return getattr(self, key, None)


@_register_bbcode
class Markdown(BBCode):
    tags = {"md", "markdown"}


@_register_bbcode
class Card(BBCode):
    tags: Final[set[str]] = {"card"}
    keys_ = {"type", "data"}

    type: str

    @property
    def card_data(self) -> str:
        return self["data"]


@_register_bbcode
class File(Card):
    keys_ = {"type", "url"}

    type: str = "file"

    @property
    def url(self) -> str:
        return self["url"]


@_register_bbcode
class Emoji(BBCode):
    tags = {"emoji"}


@_register_bbcode(0)
class B(BBCode):
    tags = {"b"}


@_register_bbcode(0)
class I(BBCode):
    tags = {"i"}


@_register_bbcode(0)
class U(BBCode):
    tags = {"u"}


@_register_bbcode(0)
class S(BBCode):
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


@_register_bbcode
class Img(BBCode):
    tags = {"img"}
    keys_ = {"width", "height"}

    @property
    def url(self) -> str:
        return self.text


@_register_bbcode
class Code(BBCode):
    tags = {"code"}


@dataclass
class MessageSegment(BaseMessageSegment["Message"]):
    data: Box

    @classmethod
    def get_message_class(cls) -> type["Message"]:
        return Message

    def __str__(self) -> str:
        return self.data["text"]

    def get_text(self) -> str:
        return self.data["text"]

    def set_text(self, text: str):
        self.data["text"] = text

    def is_text(self) -> bool:
        return self.type == "text"

    @classmethod
    def card(cls, *, text: str, type_: str, data: str) -> Self:
        return cls.build(text, [Card], {"type": type_, "data": data})

    @classmethod
    def at(cls, *, uid: str, nickname: Optional[str] = None) -> Self:
        return cls.build(nickname or uid, [At], {"at": uid})

    @classmethod
    def file(cls, *, name: str, url: str) -> Self:
        return cls.build(name, [File], {"url": url})

    @classmethod
    def url(cls, *, url: str, text: Optional[str] = None) -> Self:
        return cls.build(text or url, [Url], {"url": url})

    @classmethod
    def panel(cls, *, groupId: str, panelId: str, text: str) -> Self:
        # 同url 例如 [url=/main/group/<groupId>/<panelId>]#大厅[/url]
        return cls.build(text, [Url], {"url": f"/main/group/{groupId}/{panelId}"})

    @classmethod
    def code(cls, text: str) -> Self:
        return cls.build(text, [Code])

    @classmethod
    def text(cls, text: str, *, b: bool = False, i: bool = False, u: bool = False, s: bool = False) -> Self:
        _: list[type[BBCODE]] = []
        if b:
            _.append(B)
        if i:
            _.append(I)
        if u:
            _.append(U)
        if s:
            _.append(S)
        return cls.build(text, _)

    @classmethod
    def emoji(cls, text: str) -> Self:
        return cls.build(text, [Emoji])

    @classmethod
    def img(
        cls, url: str, *, width: Optional[Union[str, int]] = None, height: Optional[Union[str, int]] = None
    ) -> Self:
        return cls.build(url, [Img], {"width": width, "height": height})

    @classmethod
    def md(cls, text: str) -> Self:
        return cls.build(text, [Markdown])

    @classmethod
    def build(cls, text: str, tags: list[type[BBCODE]], extra: Optional[dict[str, str]] = None) -> Self:
        if extra is None:
            extra = {}
        if (length := len(tags)) == 0:
            type_ = "text"
        elif length == 1:
            type_ = tags[0].__name__.lower()
        else:
            type_ = "rich"

        _ = cls(
            type_,
            {"text": text, "extra": extra, "tags": []},
        )
        _.data["tags"] = tags
        return _

    def tag_relation(self) -> set[int]:
        return {_.relation for _ in self.tags}

    def merge_text(self, seg: Union[str, Self]) -> Self:
        self.data["text"] += seg if isinstance(self, str) else seg.get_text()
        return self

    def extend(self, seg: Self, strict: bool = True) -> Self:
        """
        新消息段的 text = self.text or seg.text
        :param seg: 要合并的消息段
        :param strict: 严格模式
        :return: 新消息段
        """
        if strict and (relations := self.tag_relation()) and any(_.relation not in relations for _ in seg.tags):
            raise ValueError("Tag relation not match")

        if self.type == "text":
            self.type = seg.type
        elif self.type != "rich":
            self.type = "rich"

        self.extra.update(seg.extra)
        self.tags.extend(seg.tags)
        self.set_text(self.get_text() or seg.get_text())
        return self

    def remove(self, bbcode: Union[BBCODE, type[BBCODE]]) -> Self:
        for _ in bbcode.keys_ | bbcode.tags:
            self.extra.pop(_, _)
        self.tags.remove(bbcode if isclass(bbcode) else type(bbcode))
        return self

    def down(self, bbcode: Union[BBCODE, type[BBCODE]]) -> Self:
        """把bbcode变为文本"""
        if bbcode is not isclass(bbcode):
            bbcode: BBCODE = self.get_tag(bbcode)
        if bbcode is None:
            return self
        bbcode: BBCODE
        self.data["text"] = str(bbcode)
        return self.remove(bbcode)

    @property
    def tags(self) -> list[type[BBCODE]]:
        return self.data["tags"]

    @property
    def extra(self) -> dict[str, str]:
        return self.data["extra"]

    def get_tag(self, bbcode: type[BBCode], index: int = 0) -> Optional[BBCODE]:
        """
        获取消息段中的BBCode
        :param bbcode: BBCode 或 子类
        :param index: 第几个，只有 bbcode=BBCode 时才有效
        :return:
        """
        if bbcode == BBCode:
            tags = self.tags
            if len(tags) > index:
                return tags[index](box=self.data)
            return None
        if bbcode in self.tags:
            return bbcode(box=self.data)
        return None

    def get_tags(self) -> list[BBCODE]:
        return [tag(box=self.data) for tag in self.tags]

    def decode(self) -> str:
        _ = deque([self.data["text"]])
        for tag in self.tags[::-1]:
            bbcode: BBCODE = tag(box=self.data)
            _.appendleft(bbcode.head)
            _.append(bbcode.tail)
        return "".join(_)

    def index(self, value: Union[str, type[BBCODE], BBCODE], raise_: bool = True) -> int:
        index = 0
        if isinstance(value, str):
            for tag in self.tags:
                if value in tag.keys_:
                    return index
                index += 1
        else:
            if not isclass(value):
                value = type(value)
            for tag in self.tags:
                if tag == value:
                    return index
                index += 1
        if raise_:
            raise ValueError(f"{value} not in list")
        return -1


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
    def get_segment_class(cls) -> type[MessageSegment]:
        return MessageSegment

    def __init__(
        self,
        message: Union[str, None, Iterable[MessageSegment], MessageSegment] = None,
    ):
        super().__init__(message)
        self.reduce()  # 合并连续的纯文本

    @classmethod
    def _construct(cls, msg: str) -> Iterable[MessageSegment]:
        yield from cls.parser.tokenize(msg)

    @classmethod
    def update_parser(cls):
        cls.parser = Parser(MessageSegment, BBCODES)

    @classmethod
    def register_bbcode(cls, code: Union[int, type[BBCODE]]):
        _register_bbcode(code)
        cls.update_parser()

    @overload
    def __getitem__(self, args: str) -> Self: ...

    @overload
    def __getitem__(self, args: tuple[str, int]) -> MessageSegment: ...

    @overload
    def __getitem__(self, args: tuple[str, slice]) -> Self: ...

    @overload
    def __getitem__(self, args: int) -> MessageSegment: ...

    @overload
    def __getitem__(self, args: slice) -> Self: ...

    @overload
    def __getitem__(self, args: type[BBCODE]) -> list[BBCODE]: ...

    @overload
    def __getitem__(self, args: tuple[type[BBCODE], int]) -> BBCODE: ...

    @overload
    def __getitem__(self, args: tuple[type[BBCODE], slice]) -> list[BBCODE]: ...

    def __getitem__(  # pyright: ignore[reportIncompatibleMethodOverride]
        self,
        args: Union[str, tuple[Union[str, type[BBCODE]], Union[int, slice]], int, slice, type[BBCODE]],
    ) -> Union[MessageSegment, Self, BBCODE, list[BBCODE]]:
        # 判断是否为 type[B]
        arg1 = args
        arg2 = slice(None)
        if isinstance(args, tuple):
            arg1, arg2 = args

        if isclass(arg1) and issubclass(arg1, BBCode):  # 是类 + 是BBCode
            return self.get_tag(arg1, arg2, strict=True) if isinstance(arg2, int) else self.get_tags(arg1)[arg2]
        return super().__getitem__(args)

    def has(self, value: Union[MessageSegment, str, type[BBCODE], BBCODE]) -> bool:
        return value in self

    def __contains__(  # pyright: ignore[reportIncompatibleMethodOverride]
        self, value: Union[MessageSegment, str, type[BBCODE], BBCODE]
    ) -> bool:
        if isinstance(value, (MessageSegment, str)):
            return super().__contains__(value)
        return value.tag_in(self)

    def index(self, value: Union[MessageSegment, str, type[BBCODE], BBCODE], *args: SupportsIndex) -> int:
        if isinstance(value, (MessageSegment, str)):
            return super().index(value, *args)
        index = 0
        for seg in self:
            _index = seg.index(value, raise_=False)
            if _index != -1:
                return _index + index
            index += len(seg.tags)
        raise ValueError(f"{value} not in list")

    def count(self, value: Union[MessageSegment, str, type[BBCode]]) -> int:
        if isinstance(value, (MessageSegment, str)):
            return super().count(value)
        return sum(1 for seg in self if value in seg.tags)

    def only(self, value: Union[MessageSegment, str, type[BBCODE]]) -> bool:
        if isinstance(value, (MessageSegment, str)):
            return super().__contains__(value)
        for seg in self:
            for tag in seg.tags:
                if tag != value:
                    return False
        return True

    def reduce(self):
        # MIT https://github.com/nonebot/adapter-onebot/blob/v2.4.3/nonebot/adapters/onebot/v11/message.py#L334-L342
        """合并消息内连续的纯文本段。"""
        index = 1
        while index < len(self):
            if len(self[index - 1].tags) == 0 and len(self[index].tags) == 0:  # 连续的纯文本
                self[index - 1].merge_text(self[index])
                del self[index]
            else:
                index += 1

    def merge_text(self) -> Self:
        if len(self) < 2:  # 只有一个消息段
            return self
        _ = [self[0]]
        for seg in self[1:]:
            seg: MessageSegment
            if len(seg.tags) == 0 and len(_[-1].tags) == 0:  # 连续的纯文本
                _[-1].merge_text(seg)
                continue
            _.append(seg)
        return Message(_)

    def extract_plain_text(self) -> str:
        return "".join(seg.data["text"] for seg in self if seg.is_text())

    def decode(self) -> str:
        return "".join(seg.decode() for seg in self)

    def show(self) -> str:
        return " ".join(seg.decode() for seg in self)

    def get_tag(self, bbcode: type[BBCode], index: int = 0, strict: bool = False) -> Optional[BBCODE]:
        if bbcode == BBCode:
            for seg in self:
                for tag in seg.tags:
                    if index == 0:
                        return tag(box=seg.data)
                    index -= 1
            if strict:
                raise IndexError(f"{bbcode} not in list")
            return None
        for seg in self:
            for tag in seg.tags:
                if tag == bbcode:
                    if index == 0:
                        return bbcode(box=seg.data)
                    index -= 1
        if strict:
            raise IndexError(f"{bbcode} not in list")
        return None

    def get_tags(self, bbcode: type[BBCode]) -> list[BBCODE]:
        if bbcode == BBCode:
            return [tag(box=seg.data) for seg in self for tag in seg.tags]
        return [tag(box=seg.data) for seg in self for tag in seg.tags if tag == bbcode]

    @property
    def tags(self) -> list[type[BBCODE]]:
        return [tag for seg in self for tag in seg.tags]
