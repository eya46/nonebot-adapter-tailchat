from yaml import safe_load

with open("api.yml", encoding="utf-8") as f:
    data = safe_load(f)


def gencode(flag):
    apis = data.items()
    apis = sorted(apis, key=lambda x: len(x[0]))
    for name, arr in apis:
        if name.startswith("plugin:"):
            continue
        if name.startswith("~"):
            continue
        strict = "!" in name[1:] or "|" in name
        use_http = "!" in name[1:]
        use_no_api = "~" in name[1:]
        name = name.strip().strip("~!|")
        if len(arr) >= 4:
            (action, ret, kv, desc) = arr[:4]
            if len(desc) > 0:
                desc = f'"""{desc}"""\n' + " " * 8
        else:
            (action, ret, kv) = arr
            desc = ""
        if "|" in name:
            name, method = name.split("|")[:2]
            name.strip()
            method.strip().lower()
        else:
            method = "post"

        kwargs = []  # 函数的参数
        kvs = [f"{action!r}"]  # call_api的参数

        if use_no_api:
            kvs.append("use_api_=False")

        if strict:
            if use_http:
                kvs.append("use_http_=True")
                kvs.append("use_sio_=False")
            else:
                kvs.append("use_http_=False")
                kvs.append("use_sio_=True")

        if method != "post":
            kvs.append(f"method={method!r}")

        for k, v in kv.items():
            kvs.append(f"{v[0]}={k}")
            if len(v) > 2:
                if v[2] is None:
                    v[2] = "Undefined"
                kwargs.append(f"{k}: {v[1]} = {v[2]}")
            else:
                kwargs.append(f"{k}: {v[1]}")

        kwargs.sort(key=lambda x: len(x) + 999 if "=" in x else len(x))  # 没有默认值的参数放在前面
        kvs[1:] = sorted(kvs[1:], key=lambda x: len(x))  # 根据参数名长度排序

        code = f"self.call_api({', '.join(kvs)})"
        code_a = "await " + code

        fret = ""
        if isinstance(ret, str):
            code = f"TypeAdapter({ret}).validate_python({code})"
            code_a = f"TypeAdapter({ret}).validate_python({code_a})"
            fret = f" -> {ret}"

        kwargs = ", *, " + ", ".join(kwargs) if kwargs else ""
        if flag:
            print(
                f"""
    def {name}(self{kwargs}){fret}:
        {desc}return {code}
"""
            )
        else:
            print(
                f"""
    async def {name}(self{kwargs}){fret}:
        {desc}return {code_a}
"""
            )


if __name__ == "__main__":
    # gencode(True)
    # print("-" * 32)
    gencode(False)
