from typing import Optional

from pydantic import BaseModel, Field, HttpUrl


class BotInfo(BaseModel):
    url: HttpUrl

    appId: Optional[str] = Field(default=None)
    appSecret: Optional[str] = Field(default=None)
    jwt: Optional[str] = Field(default=None)
    useHttp: bool = Field(default=True, description="用http<True>/socketio<False>调用接口")


class Config(BaseModel):
    bots_info: list[BotInfo] = Field(alias="tailchat_bots", default_factory=list)
    reconnect_interval: int = Field(default=5, description="重连间隔", alias="tailchat_reconnect_interval")
    time_out: int = Field(default=5, description="超时时间", alias="tailchat_time_out")
