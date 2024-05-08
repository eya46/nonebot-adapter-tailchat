from typing import Optional

from nonebot.exception import ActionFailed as BaseActionFailed
from nonebot.exception import AdapterException

from .const import ADAPTER_NAME

ERRORS: dict[str, type["ActionFailed"]] = {}


def get_error(name: str) -> Optional[type["ActionFailed"]]:
    return ERRORS.get(name, ActionFailed)


def register_error(error: type["ActionFailed"]) -> None:
    ERRORS[error.__name__] = error


class TailchatAdapterException(AdapterException):
    def __init__(self):
        super().__init__(ADAPTER_NAME)


class ActionFailed(BaseActionFailed, TailchatAdapterException):
    def __init__(self, *, name: Optional[str], code: Optional[int] = None, message: Optional[str] = None):
        super(TailchatAdapterException).__init__()
        self.name = name
        self.code = code
        self.message = message

    def __repr__(self) -> str:
        return f"ActionFailed(name={self.name!r}, code={self.code!r}, message={self.message!r})"


class DisconnectException(TailchatAdapterException): ...


class ConnectionException(TailchatAdapterException):
    def __init__(self, message: str):
        self.message = message

    def __repr__(self) -> str:
        return f"ConnectionException(message={self.message!r})"


class Error(ActionFailed):
    """通用错误"""


class DataNotFoundError(ActionFailed):
    """找不到~"""


class CastError(ActionFailed):
    """填的参数不符合规范"""


for _ in ActionFailed.__subclasses__():
    ERRORS[_.__name__] = _
