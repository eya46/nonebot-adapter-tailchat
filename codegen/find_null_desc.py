from yaml import safe_load

with open("api.yml", encoding="utf-8") as f:
    data = safe_load(f)

for k, v in data.items():
    if k.startswith("~"):
        continue
    if len(v) < 4 or v[3] == "":
        print(k)

if __name__ == "__main__":
    pass
