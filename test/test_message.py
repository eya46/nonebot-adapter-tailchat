import pytest

from nonebot_adapter_tailchat import Message, MessageSegment
from nonebot_adapter_tailchat.message import BBCode, I, Url


@pytest.mark.asyncio()
async def test_message_decode():
    # 同标签嵌套
    assert Message("[url=777][url=666]test[/url][/url]")[0].get_text() == "[url=666]test[/url]"

    # text
    message = Message("[b\n]test[i]test[/b]test[/i\n]")
    assert (
        message.decode()
        == Message(
            [
                MessageSegment.text("test", b=True),
                MessageSegment.text("test", i=True, b=True),
                MessageSegment.text("test", i=True),
            ]
        ).decode()
    )
    assert message.decode() == "[b]test[/b][b][i]test[/i][/b][i]test[/i]"
    assert (
        Message(
            [
                MessageSegment.text("test", b=True),
                MessageSegment.text("test", i=True, b=True, u=True),
                MessageSegment.text("test", i=True),
            ]
        ).decode()
        == "[b]test[/b][b][i][u]test[/u][/i][/b][i]test[/i]"
    )

    # url
    assert (
        MessageSegment.url(url="https://example.com").decode() == "[url=https://example.com]https://example.com[/url]"
    )
    assert MessageSegment.url(url="https://example.com", text="test").decode() == "[url=https://example.com]test[/url]"

    # at
    assert MessageSegment.at(uid="123").decode() == "[at=123]123[/at]"
    assert MessageSegment.at(uid="123", nickname="test").decode() == "[at=123]test[/at]"

    # emoji
    assert MessageSegment.emoji(text="smirk").decode() == "[emoji]smirk[/emoji]"

    # img
    assert (
        MessageSegment.img("https://example.com/image.jpg", width=100, height=100).decode()
        == "[img width=100 height=100]https://example.com/image.jpg[/img]"
    )
    assert (
        MessageSegment.img("https://example.com/image.jpg", height=100).decode()
        == "[img height=100]https://example.com/image.jpg[/img]"
    )

    # md
    assert MessageSegment.md("## test").decode() in ["[md]## test[/md]", "[markdown]## test[/markdown]"]

    # card
    assert (
        MessageSegment.card(text="test", type_="default", data="test").decode()
        == "[card type=default data=test]test[/card]"
    )

    # file
    assert (
        MessageSegment.file(name="test", url="https://example.com/file.txt").decode()
        == "[card url=https://example.com/file.txt type=file]test[/card]"
    )

    assert Message("[card url=https://example.com/file.txt type=file]test[/card]")[0].type == "file"
    assert Message("[card type=test data=114514]test[/card]")[0].type == "card"
    assert Message("[card url type=file]test[/card]")[0].type == "file"


@pytest.mark.asyncio()
async def test_message_extend():
    # 不可嵌套的BBCode不能合并
    with pytest.raises(ValueError):
        MessageSegment.text("test", b=True).extend(MessageSegment.md("test"))

    message = MessageSegment.text("test")
    assert message.type == "text"
    assert message.extend(MessageSegment.text("test", b=True)).type == "b"

    assert MessageSegment.text("test", b=True, i=True).type == "rich"

    message = MessageSegment.text("test", b=True).extend(MessageSegment.text("test喵", i=True))
    assert message.decode() == "[b][i]test[/i][/b]"
    assert message.type == "rich"

    assert (
        MessageSegment.text("test喵", i=True).extend(MessageSegment.text("test", b=True)).decode()
        == "[i][b]test喵[/b][/i]"
    )
    assert (
        MessageSegment.text("", i=True).extend(MessageSegment.text("test喵", b=True)).decode() == "[i][b]test喵[/b][/i]"
    )

    assert MessageSegment.code("echo tailchat 666").decode() == "[code]echo tailchat 666[/code]"


@pytest.mark.asyncio()
async def test_register_bbcode():
    assert Message("[eya46]test[/eya46]")[0].get_text() == "[eya46]test[/eya46]"

    @Message.register_bbcode
    class EYA46(BBCode):
        tags = {"eya46"}
        keys_ = {}

    assert Message("[eya46]test[/eya46]")[0].get_text() == "test"


@pytest.mark.asyncio()
async def test_message_func():
    msg = MessageSegment.url(url="https://example.com")
    assert Url.tag_in(msg)

    msg = Message([MessageSegment.text("test", i=True), MessageSegment.url(url="https://example.com")])
    assert Url.tag_in(msg)
    assert Url in msg
    assert I.tag_in(msg)
    assert I in msg

    url = msg.get_tag(Url)
    assert url.tag_in(msg)
    assert url in msg


@pytest.mark.asyncio()
async def test_message_contains():
    message = (
        Message("test")
        + MessageSegment.url(url="https://example.com")
        + MessageSegment.text("test", i=True)
        + MessageSegment.text("test", b=True, i=True)
    )
    assert message.has("text") and "text" in message
    assert message.has("url") and "url" in message
    assert message.has("i") and "i" in message
