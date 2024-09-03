import os

import nonebot
import pytest
from nonebug import NONEBOT_INIT_KWARGS

# 导入适配器
from nonebot_adapter_tailchat import Adapter as TailchatAdapter

os.environ["ENVIRONMENT"] = "test"


def pytest_configure(config: pytest.Config):
    config.stash[NONEBOT_INIT_KWARGS] = {"secret": os.getenv("INPUT_SECRET")}


@pytest.fixture(scope="session", autouse=True)
def load_bot():
    # 加载适配器
    driver = nonebot.get_driver()
    driver.register_adapter(TailchatAdapter)

    # 加载插件
    nonebot.load_plugins("plugins")

    return None
