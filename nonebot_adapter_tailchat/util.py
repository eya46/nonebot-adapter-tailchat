from asyncio import sleep
from functools import wraps
from io import StringIO
from traceback import print_exc
from typing import Any, Optional, Union

from msgpack import ExtType
from nonebot.utils import logger_wrapper

from .const import ADAPTER_NAME

EXT = {0: lambda _: int.from_bytes(_, byteorder="big")}


def unpack(data: Union[ExtType, any]) -> Any:
    if isinstance(data, ExtType) and data.code in EXT:
        return EXT[data.code](data.data)
    return data


class Log:
    def __init__(self):
        self.log = logger_wrapper(ADAPTER_NAME)

    def __call__(self, level: str, message: str, exception: Optional[Exception] = None):
        self.log(level, message, exception)

    def success(self, *args, exception: Optional[Exception] = None):
        _ = StringIO()
        print(*args, file=_, end="")
        self.log("SUCCESS", _.getvalue(), exception)

    def info(self, *args, exception: Optional[Exception] = None):
        _ = StringIO()
        print(*args, file=_, end="")
        self.log("INFO", _.getvalue(), exception)

    def debug(self, *args, exception: Optional[Exception] = None):
        _ = StringIO()
        print(*args, file=_, end="")
        self.log("DEBUG", _.getvalue(), exception)

    def error(self, *args, exception: Optional[Exception] = None):
        _ = StringIO()
        print(*args, file=_, end="")
        self.log("ERROR", _.getvalue(), exception)

    def warning(self, *args, exception: Optional[Exception] = None):
        _ = StringIO()
        print(*args, file=_, end="")
        self.log("WARNING", _.getvalue(), exception)

    def trace(self, *args, exception: Optional[Exception] = None):
        _ = StringIO()
        print(*args, file=_, end="")
        self.log("TRACE", _.getvalue(), exception)


log = Log()


def retry(wait_time: int, func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            await func(*args, **kwargs)
        except Exception as e:
            log.error(f"Error when exec {func.__name__}: {repr(e)}")
            print_exc()
        await sleep(wait_time)

    return wrapper
