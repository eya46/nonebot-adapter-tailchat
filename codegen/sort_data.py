from collections import OrderedDict

from yaml import safe_dump, safe_load

with open("api.yml", encoding="utf8") as f:
    openapi: dict = safe_load(f)

res = OrderedDict()

with open("api.yml", "w", encoding="utf8") as f:
    safe_dump(
        dict(sorted(openapi.items(), key=lambda x: len(x[0]) if not x[0].startswith("~") else len(x[0]) + 999)),
        f,
        indent=4,
        allow_unicode=True,
        sort_keys=False,
    )
