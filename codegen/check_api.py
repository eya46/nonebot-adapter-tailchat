import httpx
import yarl
from yaml import safe_dump, safe_load

with open("api.yml", encoding="utf-8") as f:
    data = safe_load(f)

unuseful = []

for k, v in data.items():
    web = httpx.get(str(yarl.URL("https://tailchat-nightly.moonrailgun.com/api") / v[0].replace(".", "/")))
    if web.status_code == 404:
        print(k)
        unuseful.append(k)

for k in unuseful:
    data[f"~{k}"] = data[k]
    del data[k]

with open("api.yml", "w", encoding="utf-8") as f:
    safe_dump(data, f, indent=4, allow_unicode=True)

if __name__ == "__main__":
    pass
