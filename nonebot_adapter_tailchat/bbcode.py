# BSD-2-Clause license
# https://github.com/dcwatson/bbcode/blob/master/bbcode.py
"""
Copyright (c) 2011, Dan Watson.
All rights reserved.

Redistribution and use in source and binary forms, with or without modification,
are permitted provided that the following conditions are met:

    1. Redistributions of source code must retain the above copyright notice,
       this list of conditions and the following disclaimer.

    2. Redistributions in binary form must reproduce the above copyright
       notice, this list of conditions and the following disclaimer in the
       documentation and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

from collections import OrderedDict, defaultdict, deque
from shlex import split
from sys import getrecursionlimit
from typing import TYPE_CHECKING, Union

if TYPE_CHECKING:
    from .message import B, MessageSegment


class Parser:
    def __init__(
        self,
        seg: type["MessageSegment"],
        tags: dict[str, type["B"]],
        drop_unrecognized=False,
        max_tag_depth=None,
    ):
        self.seg = seg
        self.tag_opener = "["
        self.tag_closer = "]"
        self.tags = tags
        self.drop_unrecognized = drop_unrecognized
        self.max_tag_depth = max_tag_depth or getrecursionlimit()

    def _parse_opts(self, data):
        opts = OrderedDict()
        args = split(data)
        tag, args = args[0], args[1:]

        if "=" in tag:
            name, opts[name.lower()] = tag.split("=", 1)
        else:
            name = tag

        for arg in args:
            if "=" in arg:
                k, v = arg.split("=", 1)
                opts[k.lower()] = v
            else:
                opts[arg.lower()] = ""
        return name.lower(), opts

    def _parse_tag(self, tag):
        """
        Given a tag string (characters enclosed by []), this function will
        parse any options and return a tuple of the form:
            (valid, tag_name, closer, options)
        """
        if not tag.startswith(self.tag_opener) or not tag.endswith(self.tag_closer):
            return False, tag, False, None
        tag_name = tag[len(self.tag_opener) : -len(self.tag_closer)].strip()
        if not tag_name:
            return False, tag, False, None
        closer = False
        opts = {}
        if tag_name[0] == "/":
            tag_name = tag_name[1:]
            closer = True
        # Parse options inside the opening tag, if needed.
        if (("=" in tag_name) or (" " in tag_name)) and not closer:
            tag_name, opts = self._parse_opts(tag_name)
        return True, tag_name.strip().lower(), closer, opts

    def _tag_extent(self, data, start):
        """
        Finds the extent of a tag, accounting for option quoting and new tags starting before the current one closes.
        Returns (found_close, end_pos) where valid is False if another tag started before this one closed.
        """
        in_quote = False
        quotable = False
        lto = len(self.tag_opener)
        ltc = len(self.tag_closer)
        for i in range(start + 1, len(data)):
            ch = data[i]
            if ch == "=":
                quotable = True
            if ch in ('"', "'"):
                if quotable and not in_quote:
                    in_quote = ch
                elif in_quote == ch:
                    in_quote = False
                    quotable = False
            if not in_quote and data[i : i + lto] == self.tag_opener:
                return i, False
            if not in_quote and data[i : i + ltc] == self.tag_closer:
                return i + ltc, True
        return len(data), False

    def tokenize(self, data):
        data = data.replace("\r\n", "\n").replace("\r", "\n")
        pos = 0
        ld = len(data)
        tokens: list[Union["MessageSegment", tuple["MessageSegment", str, str]]] = []
        tags: dict[str, deque["MessageSegment"]] = defaultdict(deque)
        while pos < ld:
            start = data.find(self.tag_opener, pos)  # 寻找下一个标签开始

            if start >= pos:
                if start > pos:  # 标签之间的内容
                    tokens.append(self.seg.text(data[pos:start]))
                # Find the extent of this tag, if it's ever closed.
                end, found_close = self._tag_extent(data, start)
                pos = end
                if found_close:
                    tag = data[start:end]
                    valid, tag_name, closer, opts = self._parse_tag(tag)
                    # Make sure this is a well-formed, recognized tag, otherwise it's just data.
                    if valid and tag_name in self.tags:
                        if closer:
                            if len(tags[tag_name]) == 0:  # 未找到对应的开始标签
                                tokens.append(self.seg.text(tag))
                                continue
                            # 从右到左, 找到第一个匹配的未闭合的标签, 找到后将其闭合
                            # 期间的表判断 1. tags为空 则加入其中
                            # 2. 有tag, 判断relation, 如果不相同的relation则把其中tag变成text, 并加入tag.
                            #   相同则直接加入tag
                            tag_start = tags[tag_name].pop()
                            bbcode_start = tag_start.data["tags"][0]
                            for i in tokens[::-1]:
                                if isinstance(i, self.seg):  # 是纯文本
                                    if len(i.data["tags"]) == 0:
                                        i.extend(tag_start)
                                    else:
                                        if any(_.relation != bbcode_start.relation for _ in i.data["tags"][:]):
                                            for _ in i.data["tags"][::-1]:
                                                i.down(_)
                                        i.extend(tag_start)
                                else:  # 是标签
                                    _tag_name = i[1]
                                    if _tag_name == tag_name:
                                        tokens.remove(i)
                                        break
                        else:
                            seg = self.seg.build("", [self.tags[tag_name]], opts)
                            tags[tag_name].append(seg)
                            tokens.append((seg, tag_name, tag))
                    elif valid and self.drop_unrecognized and tag_name not in self.tags:
                        # If we found a valid (but unrecognized) tag and self.drop_unrecognized is True, just drop it.
                        pass
                    else:
                        tokens.append(self.seg.text(tag))
                else:
                    # We didn't find a closing tag, tack it on as text.
                    tokens.append(self.seg.text(data[start:end]))

            else:  # 没找到标签开始
                break
        if pos < ld:  # 剩余文本
            tokens.append(self.seg.text(data[pos:]))
        for idx, t in enumerate(tokens):
            if not isinstance(t, self.seg):  # 未闭合的标签
                tokens[idx] = self.seg.text(t[2])
        return self.seg.get_message_class()(tokens)
