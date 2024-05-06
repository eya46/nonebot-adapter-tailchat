<p align="center">
  <a href="https://nonebot.dev/"><img src="https://nonebot.dev/logo.png" width="200" height="200" alt="nonebot"></a>
</p>

<div align="center">

# Nonebot Adapter Tailchat

## Tailchat 适配器

![License](https://img.shields.io/github/license/eya46/nonebot-adapter-tailchat)
![Python](https://img.shields.io/badge/python-3.9+-blue.svg)
![NoneBot](https://img.shields.io/badge/nonebot-2.3.0+-red.svg)
</div>

## 环境要求

- Python 3.9+
- NoneBot 2.3.0+
- pydantic >= 2.0.0
- HTTPClient驱动器
    - > 默认需要,除非 `useHttp=False`, 且配置了 `jwt`
    - ~httpx
    - ~aiohttp

## Tailchat机器人开启方式

1. 安装 `开放平台插件`
2. 进入 `设置` -> `开放平台` -> `创建应用` -> `填写基本信息`
3. 进入 `应用` -> `机器人` -> `开启机器人能力`
4. 在 `基本信息` 内获取 `appId` 和 `appSecret`

> 暂未支持 `消息回调地址`

## 配置方式

`.env` 文件

```dotenv
TAILCHAT_BOTS='
[
  {
    "url": "https://xxxxxxx/",
    "appId": "ts_******",
    "appSecret": "****"
  }
]
'

TAILCHAT_RECONNECT_INTERVAL=5
TAILCHAT_TIME_OUT=5
```

## 详细配置项

[config.py](./nonebot_adapter_tailchat/config.py)

## 相关项目
- [dcwatson/bbcode](https://github.com/dcwatson/bbcode)
- [Tailchat](https://github.com/msgbyte/tailchat)
- [python-socketio](https://github.com/miguelgrinberg/python-socketio)
- [nonebot2](https://github.com/nonebot/nonebot2)
- [pydantic2](https://docs.pydantic.dev/latest/)
- ...