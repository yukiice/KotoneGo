# 14 文件与数据格式

> 主题标签：`files` ｜ 对应考试主题：文件与数据格式

## 14.1 打开文件：永远用 with

```python
# ✅ 推荐：自动关闭、异常安全
with open("data.txt", "r", encoding="utf-8") as f:
    content = f.read()

# ❌ 容易忘记 close，异常时可能泄漏文件描述符
f = open("data.txt", encoding="utf-8")
content = f.read()
f.close()
```

>`open()` 的默认编码依赖平台（Windows 常是 cp936/gbk），**显式写 `encoding="utf-8"`** 是跨平台正确性的关键。

## 14.2 模式一览

| 模式 | 含义 | 文件不存在 | 是否清空 |
| --- | --- | --- | --- |
| `"r"` | 只读（默认） | `FileNotFoundError` | 否 |
| `"w"` | 只写 | 创建 | **是（截断）** |
| `"a"` | 追加 | 创建 | 否（从末尾写） |
| `"x"` | 独占创建 | 创建 | 若已存在则 `FileExistsError` |
| `"r+"` | 读写 | 报错 | 否 |
| `"rb"` / `"wb"` | 二进制 | 同 r/w | 同 w |
| `"r+b"` | 二进制读写 | 报错 | 否 |

```python
with open("out.txt", "w", encoding="utf-8") as f:
    f.write("hello\n")

with open("out.txt", "a", encoding="utf-8") as f:
    f.write("append\n")

with open("img.png", "rb") as f:
    header = f.read(8)        # bytes
```

> 二进制模式下**不能**传 `encoding`。

## 14.3 读取方式对比

```python
with open("big.log", encoding="utf-8") as f:
    text = f.read()             # 全部内容 -> str（大文件慎用）
    lines = f.readlines()       # 全部行 -> list[str]（大文件慎用）

with open("big.log", encoding="utf-8") as f:
    first = f.readline()        # 读一行
    rest = f.read()             # 读剩余

# ✅ 大文件：逐行惰性迭代，内存恒定
with open("big.log", encoding="utf-8") as f:
    for line in f:
        process(line.rstrip("\n"))
```

内存占用对比：

| 方式 | 内存 |
| --- | --- |
| `f.read()` | O(文件大小) |
| `f.readlines()` | O(文件大小) |
| `for line in f` | O(一行) |

## 14.4 写入与缓冲

```python
with open("log.txt", "w", encoding="utf-8") as f:
    f.write("第一行\n")
    f.writelines(["a\n", "b\n"])     # 注意：不会自动加换行符
    f.flush()                        # 手动刷缓冲（一般不需要）
```

- 写操作有缓冲区，`with` 结束时 close 会 flush，保证落盘。
- 需要“立刻可见”（如日志被其他进程读取）时用 `flush=True` 或 `f.flush()`。
- 强制落盘：`os.fsync(f.fileno())`。

## 14.5 路径处理：pathlib 优先

```python
from pathlib import Path

p = Path("data") / "users.json"        # 跨平台拼接（不写 "/" 或 "\\"）
print(p.name, p.stem, p.suffix, p.parent)
print(p.exists(), p.is_file(), p.is_dir())

p.parent.mkdir(parents=True, exist_ok=True)     # 幂等建目录
p.write_text('{"a": 1}', encoding="utf-8")
data = p.read_text(encoding="utf-8")

# 遍历
for child in Path(".").iterdir():
    print(child)
for py in Path("src").rglob("*.py"):            # 递归匹配
    print(py)

# 常用操作
print(Path("a.txt").resolve())          # 绝对路径
print(Path("a/b/c.txt").with_suffix(".md"))   # a/b/c.md
p.rename("new.json")                    # 重命名/移动
p.unlink(missing_ok=True)               # 删除文件（不存在也不报错）
```

传统 `os.path` 写法（老代码常见）：

```python
import os
os.path.join("data", "users.json")
os.path.exists("data")
os.makedirs("data", exist_ok=True)
os.listdir("data")
```

新代码优先 `pathlib`。

## 14.6 JSON

```python
import json

data = {"name": "Alice", "tags": ["py", "ts"], "age": 30}

# 对象 <-> 字符串
text = json.dumps(data, ensure_ascii=False, indent=2)   # ensure_ascii=False 保留中文
obj = json.loads(text)

# 文件
from pathlib import Path
Path("user.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

with open("user.json", encoding="utf-8") as f:
    loaded = json.load(f)          # load = 从文件读

with open("user.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
```

命名规律：**带 s 的操作字符串（string），不带 s 的操作文件**。

支持的 Python 类型：`dict, list, str, int, float, bool, None`。
不支持的会抛 `TypeError`：

```python
import datetime
json.dumps({"t": datetime.datetime.now()})       # ❌ TypeError

json.dumps({"t": datetime.datetime.now()}, default=str)     # ✅ 转字符串
# 或先手动转换
json.dumps({"t": datetime.datetime.now().isoformat()})
# dataclass
from dataclasses import asdict
json.dumps(asdict(obj), ensure_ascii=False)
```

解析失败：

```python
try:
    json.loads("{bad json")
except json.JSONDecodeError as exc:
    print("JSON 无效", exc.lineno, exc.colno)
```

大文件流式解析：

```python
# pip install ijson
# import ijson
# with open("big.json", "rb") as f:
#     for item in ijson.items(f, "items.item"):
#         ...
```

## 14.7 CSV

```python
import csv

# 写
with open("users.csv", "w", encoding="utf-8", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["id", "name"])
    writer.writerows([[1, "Alice"], [2, "Bob"]])

# 读
with open("users.csv", encoding="utf-8", newline="") as f:
    for row in csv.reader(f):
        print(row)          # ['1', 'Alice']  ← 都是字符串

# 字典方式（推荐）
with open("users.csv", encoding="utf-8", newline="") as f:
    for row in csv.DictReader(f):
        print(row["name"], int(row["id"]))

with open("users.csv", "w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["id", "name"])
    writer.writeheader()
    writer.writerow({"id": 1, "name": "Alice"})
```

要点：

- 打开 CSV 文件要加 `newline=""`，否则 Windows 上会出现空行。
- 读出来全是字符串，需要自己转换类型。
- 字段含逗号/换行/引号时，csv 模块会自动加引号处理（手写 `split(",")` 会出错）。

## 14.8 其他格式

```python
# 环境变量风格的 .env（自己解析，见第 13 章）
# TOML（3.11+ 标准库）
import tomllib
with open("pyproject.toml", "rb") as f:      # 注意：二进制模式
    cfg = tomllib.load(f)

# YAML（第三方）
# pip install pyyaml
# import yaml; yaml.safe_load(text)

# pickle（仅限可信数据）
import pickle
raw = pickle.dumps({"a": 1})
print(pickle.loads(raw))
```

> **安全警告**：`pickle` 反序列化会执行任意代码，绝不能用于来自网络或用户的数据。对外交换用 JSON / CSV / MessagePack。

## 14.9 目录级操作

```python
import shutil
from pathlib import Path

shutil.copy("a.txt", "backup/a.txt")
shutil.copytree("src", "src_backup", dirs_exist_ok=True)
shutil.move("old", "new")
shutil.rmtree("tmp_dir")           # 递归删除（危险）
shutil.disk_usage("/").free        # 磁盘剩余
```

临时文件：

```python
import tempfile
from pathlib import Path

with tempfile.TemporaryDirectory() as tmp:
    p = Path(tmp) / "x.txt"
    p.write_text("hi", encoding="utf-8")

with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
    f.write("{}")
```

## 14.10 常见错误速查

| 错误 | 原因 | 修复 |
| --- | --- | --- |
| `FileNotFoundError` | 路径不存在 / 父目录没建 | `mkdir(parents=True, exist_ok=True)` |
| `PermissionError` | 无权限 | 检查路径与权限 |
| `UnicodeDecodeError` | 编码不对 | 指定正确 `encoding` 或 `errors="replace"` |
| `IsADirectoryError` | 把目录当文件打开 | 检查路径 |
| 写完文件没内容 | 没 close/flush | 用 `with` |
| CSV 多出空行 | 没加 `newline=""` | 加上 |
| `TypeError: write() argument must be str` | 文本模式写了 bytes | 用 `"wb"` 或先 decode |
| 写中文乱码 | 未指定 UTF-8 | `encoding="utf-8"` |

## 14.11 与 JS/TS 对照

| 需求 | TypeScript（Node） | Python |
| --- | --- | --- |
| 同步读 | `fs.readFileSync(p, "utf8")` | `Path(p).read_text(encoding="utf-8")` |
| 同步写 | `fs.writeFileSync(p, s)` | `Path(p).write_text(s, encoding="utf-8")` |
| 流式读 | `fs.createReadStream` | `for line in f:` |
| 路径拼接 | `path.join(a, b)` | `Path(a) / b` |
| 目录创建 | `fs.mkdirSync(p, {recursive:true})` | `Path(p).mkdir(parents=True, exist_ok=True)` |
| JSON | `JSON.parse/stringify` | `json.loads/dumps` |
| 异步 IO | 默认异步 API | asyncio + aiofiles |
| 临时目录 | `os.tmpdir()` + 手写 | `tempfile.TemporaryDirectory()` |

## 14.12 小练习

```python
# 1. 逐行处理大文件并统计
from collections import Counter
from pathlib import Path

def count_status(path: str) -> Counter:
    result = Counter()
    with open(path, encoding="utf-8") as f:
        for line in f:
            parts = line.split()
            if parts:
                result[parts[-1]] += 1
    return result

# 2. JSON 配置读写（带默认值合并）
def load_config(path: str, defaults: dict) -> dict:
    p = Path(path)
    if not p.exists():
        return dict(defaults)
    data = json.loads(p.read_text(encoding="utf-8"))
    return {**defaults, **data}
```

- [ ] 我知道 `"w"` 会清空文件，追加要用 `"a"`。
- [ ] 我知道读大文件应该逐行迭代。
- [ ] 我知道 `json.dumps` / `json.dump` 的区别。
- [ ] 我知道为什么不应该用 pickle 处理不可信数据。
- [ ] 我知道写文本要显式指定 `encoding="utf-8"`。
