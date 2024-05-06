import nonebot

from nonebot_adapter_tailchat import Adapter as TailchatAdapter

nonebot.init()

driver = nonebot.get_driver()
driver.register_adapter(TailchatAdapter)

nonebot.load_builtin_plugin("echo")
nonebot.load_plugins("plugins")

if __name__ == "__main__":
    nonebot.run()
