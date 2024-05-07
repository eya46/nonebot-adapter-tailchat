import pytest

from nonebot_adapter_tailchat import Message, MessageSegment
from nonebot_adapter_tailchat.message import BBCode


@pytest.mark.asyncio()
async def test_message_decode():
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
        == "[file url=https://example.com/file.txt]test[/file]"
    )


@pytest.mark.asyncio()
async def test_message_extend():
    # 不可嵌套的BBCode不能合并
    with pytest.raises(ValueError):
        MessageSegment.text("test", b=True).extend(MessageSegment.md("test"))

    assert (
        MessageSegment.text("test", b=True).extend(MessageSegment.text("test喵", i=True)).decode()
        == "[b][i]test[/i][/b]"
    )
    assert (
        MessageSegment.text("test喵", i=True).extend(MessageSegment.text("test", b=True)).decode()
        == "[i][b]test喵[/b][/i]"
    )
    assert (
        MessageSegment.text("", i=True).extend(MessageSegment.text("test喵", b=True)).decode() == "[i][b]test喵[/b][/i]"
    )


@pytest.mark.asyncio()
async def test_register_bbcode():
    assert Message("[eya46]test[/eya46]")[0].get_text() == "[eya46]test[/eya46]"

    @Message.register_bbcode
    class EYA46(BBCode):
        tags = {"eya46"}
        keys_ = {}

    assert Message("[eya46]test[/eya46]")[0].get_text() == "test"
