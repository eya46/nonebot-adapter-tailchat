from typing import Optional

from nonebot.exception import ActionFailed as BaseActionFailed
from nonebot.exception import AdapterException

from .const import ADAPTER_NAME


class TailchatAdapterException(AdapterException):
    def __init__(self):
        super().__init__(ADAPTER_NAME)


class ActionFailed(BaseActionFailed, TailchatAdapterException):
    def __init__(self, *, code: Optional[int] = None, message: Optional[str] = None):
        super(TailchatAdapterException).__init__()
        self.code = code
        self.message = message

    def __repr__(self) -> str:
        return f"ActionFailed(code={self.code!r}, message={self.message!r})"


class DisconnectException(TailchatAdapterException):
    def __init__(self):
        super().__init__()
