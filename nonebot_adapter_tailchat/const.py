from typing import TypeVar, Union

ADAPTER_NAME = "Tailchat"


class Undefined:
    pass


_ = TypeVar("_")

Optional = Union[type(None), type(Undefined), _]
