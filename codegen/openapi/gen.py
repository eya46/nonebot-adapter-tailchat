from json import load

from yaml import safe_dump, safe_load

openapi = {}

with open("openapi.json") as f:
    openapi["paths"] = load(f)["paths"]

with open("openapi.yaml") as f:
    openapi["paths"].update(safe_load(f)["paths"])

with open("../api.yml", encoding="utf8") as f:
    exist = safe_load(f)

filters = ["debug"]


def check_func_name(name):
    return {
        "type": "type_",
    }.get(name, name)


def js2py(js):
    return {
        "string": "str",
        "number": "int",
        "object": "dict",
        "array": "list",
        "boolean": "bool",
        "any": "Any",
    }.get(js, js)


def get_properties(scheme):
    if "properties" in scheme:
        for k, v in scheme["properties"].items():
            if isinstance(v, list):
                v = v[0]
                # v["items"] = v["type"]
                # v["type"] = "array"
            name = check_func_name(k)
            type_name = v["type"]
            optional = v.get("optional", False)
            if type_name == "array":
                type_ = v.get("items", "str")
                type_ = js2py(type_)
                yield (name, k, f"Optional[list[{type_}]]", None) if optional else (name, k, f"list[{type_}]")
            elif type_name in ["string", "email"]:
                yield (name, k, "Optional[str]", None) if optional else (name, k, "str")
            elif type_name == "number":
                yield (name, k, "Optional[int]", None) if optional else (name, k, "int")
            elif type_name == "any":
                yield (name, k, "Optional[Any]", None) if optional else (name, k, "Any")
            elif type_name == "object":
                yield (name, k, "Optional[dict]", None) if optional else (name, k, "dict")
            elif type_name == "enum":
                _data = [f"'{i}'" for i in v["values"]]
                _data = f"Literal[{', '.join(_data)}]"
                yield (name, k, f"Optional[{_data}]", None) if optional else (name, k, _data)
            else:
                raise ValueError(f"unknown type {type_name}")
    else:
        scheme = scheme["oneOf"]

        each = [set(get_properties(i)) for i in scheme]
        intersection = set.intersection(*each)
        union = set.union(*each)
        yield from intersection
        for i in union - intersection:
            yield check_func_name(i[0]), i[0], f"Optional[{i[1]}]", None


a1 = []

for k, v in openapi["paths"].items():
    if any(i in k for i in filters):
        continue
    k: str = k[1:].replace("/", ".")
    if k.startswith("api."):
        k = k[4:]
    v = v["post"]

    desc = v.get("summary", "")
    # print("开始", k, desc)
    schemes = get_properties(v["requestBody"]["content"]["application/json"]["schema"])
    names = k.split(".")
    if not k.startswith("plugin:"):
        if len(names[-1]) < 7:
            name = names[-1] + names[-2].capitalize()
        else:
            name = names[-1]
    else:
        name = k
    if name in a1:
        print("!!!重复api", k, name)
        continue
    a1.append(name)
    if ":" in name:
        # name = "_".join(name.split(":"))
        continue
    if "." in name:
        name = name.split(".")
        name = name[0] + "".join(i.capitalize() for i in name[1:])
    flag = False
    for k_, v_ in exist.items():
        if k == v_[0]:
            flag = True
            kvs = {j[0]: j[1:] for j in schemes}
            exist[k_] = [k, v_[1] if isinstance(v_[1], str) else tuple(v_[1]), kvs if len(kvs)>len(v_[2]) else v_[2], v_[3]]
            break
    if not flag:
        exist[name] = [k, [None, None], {j[0]: j[1:] for j in schemes}, desc]
    # print(k, desc, *schemes)

    # for i in v.keys():
    #     desc = v[i].get("summary", "")
    #
    #     if i == "post":
    #         schemes = get_properties(v["post"]["requestBody"]["content"]["application/json"]["schema"])
    #         api[k] = [
    #             k, None, {
    #                 j[0]: j[1:] for j in schemes
    #             },
    #             desc
    #         ]
    #         print(k, desc, *schemes)
    #     else:
    #         print(f"{k}|{i}", k, desc)

# print(dumps(api, indent=4, ensure_ascii=True))
# print(exist)
# print("-" * 64)
print(
    safe_dump(
        dict(sorted(exist.items(), key=lambda x: len(x[0]) if not x[0].startswith("~") else len(x[0]) + 999)),
        indent=4,
        allow_unicode=True,
        sort_keys=False,
    )
)

if __name__ == "__main__":
    pass
