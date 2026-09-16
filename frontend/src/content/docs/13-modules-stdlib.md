# 13 模块、包与标准库

> 主题标签：`modules` ｜ 对应考试主题：模块、包与标准库

## 13.1 模块与包的层次

```
myapp/                      ← 项目根（通常也是仓库根）
├── pyproject.toml
├── src/
│   └── myapp/              ← 包（package）
│       ├── __init__.py
│       ├── main.py         ← 模块（module）
│       ├── config.py
│       └── routers/        ← 子包
│           ├── __init__.py
│           └── users.py
└── tests/
```

- **模块** = 一个 `.py` 文件。
- **包** = 有 `__init__.py` 的目录（Python 3.3+ 也支持无 `__init__.py` 的命名空间包，但常规项目仍会保留）。
- **导入路径**用点号表示层级：`myapp.routers.users`。

## 13.2 导入语法

```python
import math                       # 引入模块，用 math.pi
import numpy as np                # 别名（社区惯例）
from math import sqrt, pi         # 直接引入名字
from math import sqrt as sq       # 重命名
from .utils import helper         # 相对导入（当前包）
from ..core import settings       # 上一级包
```

**不要**使用 `from math import *`：污染命名空间、来源不明、可能覆盖已有名字。若确实要导出多个名字，用 `__all__` 明确声明：

```python
# myapp/utils.py
__all__ = ["slugify", "truncate"]

def slugify(text: str) -> str: ...
def truncate(text: str, n: int) -> str: ...
def _internal(): ...        # 不在 __all__ 中，下划线表示内部
```

## 13.3 导入的执行时机与缓存

```python
# a.py
print("a 被导入")

# b.py
import a      # 打印 "a 被导入"
import a      # 不再打印（sys.modules 缓存）
```

- 模块首次导入时执行其顶层代码，之后复用 `sys.modules` 里的对象。
- 因此“模块级全局变量”天然是单例，可用于缓存/连接池（但要考虑线程安全）。
- 循环导入（a 导入 b，b 导入 a）会导致 `ImportError` 或部分初始化的模块，**解决方式**：把 import 放进函数内、提取公共模块，或只在类型注解中使用 `if TYPE_CHECKING`。

```python
from typing import TYPE_CHECKING
if TYPE_CHECKING:                 # 只给类型检查器看，运行时不导入
    from .models import User
```

## 13.4 `__name__` 与入口

```python
if __name__ == "__main__":
    main()
```

| 运行方式 | `__name__` |
| --- | --- |
| `python app/main.py` | `"__main__"` |
| `import app.main` | `"app.main"` |
| `python -m app.main` | `"__main__"` |

推荐用 `python -m package.module` 运行包内模块，能正确解析包上下文。

## 13.5 标准库必会清单

### 文件与路径

```python
from pathlib import Path

p = Path("data") / "users.json"
p.exists(); p.is_file(); p.suffix; p.stem; p.parent
p.mkdir(parents=True, exist_ok=True)
p.write_text("hi", encoding="utf-8")
print(p.read_text(encoding="utf-8"))
print(list(Path(".").glob("**/*.py"))[:5])
```

### 数据格式

```python
import json, csv, tomllib        # tomllib 是 3.11+
json.dumps({"a": 1}, ensure_ascii=False, indent=2)
json.loads('{"a": 1}')
tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
```

### 时间

```python
from datetime import datetime, timedelta, timezone

now = datetime.now(timezone.utc)          # aware（带时区）
print(now.isoformat(timespec="seconds"))
print((now + timedelta(days=1)).date())
print(now.strftime("%Y-%m-%d %H:%M"))
print(datetime.fromisoformat("2024-05-01T10:00:00+08:00"))
```

### 随机与安全

```python
import random, secrets
random.random()            # [0.0, 1.0)
random.randint(1, 6)       # 含两端
random.choice(["a", "b"])  # 随机取一个
random.sample(range(100), 10)   # 不重复抽样
random.shuffle(items)      # 原地打乱
secrets.token_hex(16)      # 密码学安全随机（令牌、密码）
```

### 字符串与正则

```python
import re
re.search(r"\d+", "abc123").group()      # '123'
re.findall(r"\w+", "a b c")              # ['a', 'b', 'c']
re.sub(r"\s+", " ", "a   b")             # 'a b'
re.split(r"[,;]", "a,b;c")               # ['a', 'b', 'c']
m = re.match(r"(?P<y>\d{4})-(?P<m>\d{2})", "2024-05")
print(m.group("y"), m.group("m"))        # 2024 05
```

> 正则一律用原始字符串 `r"..."`，避免 `\d` 被当转义。

### 常用工具模块

```python
import os, sys, math, statistics, json, pathlib
from collections import Counter, defaultdict, deque, OrderedDict
from itertools import count, chain, islice, groupby, product
from functools import lru_cache, partial, reduce, wraps
import argparse           # 命令行参数
import logging            # 日志
import sqlite3            # 内置数据库
import asyncio            # 异步（第 17 章）
import unittest / doctest # 测试（更推荐 pytest）
```

## 13.6 日志（比 print 更专业）

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

logger.debug("调试细节")
logger.info("启动成功，端口 %s", 8000)      # 用 % 风格延迟格式化
logger.warning("磁盘剩余不足")
try:
    1 / 0
except ZeroDivisionError:
    logger.exception("计算失败")            # 自动带上 traceback
```

级别从低到高：`DEBUG < INFO < WARNING < ERROR < CRITICAL`。

## 13.7 命令行参数（argparse）

```python
import argparse

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="示例 CLI")
    parser.add_argument("path", help="输入文件")
    parser.add_argument("-n", "--num", type=int, default=10)
    parser.add_argument("--verbose", action="store_true")
    return parser

if __name__ == "__main__":
    args = build_parser().parse_args()
    print(args.path, args.num, args.verbose)
```

更现代的替代：`typer`、`click`（第三方）。

## 13.8 环境变量与配置

```python
import os
from pathlib import Path

DEBUG = os.getenv("DEBUG", "false").lower() == "true"
PORT = int(os.getenv("PORT", "8000"))
DB_PATH = Path(os.getenv("DB_PATH", "data/app.db"))

# .env 文件（标准库不解析，可用 python-dotenv 或自己写）
def load_dotenv(path: str = ".env") -> None:
    p = Path(path)
    if not p.exists():
        return
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip("\"'"))

load_dotenv()
```

> 本项目后端就是用这种方式读取 `KOTONE_DB_PATH`、`KOTONE_EXAM_SIZE` 等配置。

## 13.9 pip 与依赖管理

```bash
pip install requests                  # 安装
pip install "fastapi>=0.115"          # 指定版本约束
pip install -r requirements.txt       # 从清单安装
pip list                              # 已安装列表
pip show fastapi                      # 包详情
pip uninstall requests
pip freeze > requirements.txt         # 导出完整快照
```

现代项目结构（PEP 621）：

```toml
# pyproject.toml
[project]
name = "kotone"
version = "0.0.1"
requires-python = ">=3.11"
dependencies = ["fastapi>=0.115", "uvicorn[standard]>=0.30"]

[project.optional-dependencies]
dev = ["pytest", "ruff", "mypy"]

[tool.ruff]
line-length = 100

[tool.mypy]
strict = true
```

```bash
pip install -e ".[dev]"        # 可编辑安装 + 开发依赖
uv sync                        # 若使用 uv 包管理器
```

## 13.10 与 JS/TS 对照

| 需求 | TypeScript | Python |
| --- | --- | --- |
| 导入 | `import x from "./x"` | `from .x import y` |
| 默认导出 | `export default` | 顶层名字默认可见（`__all__` 控制 `*`） |
| 包管理 | npm / pnpm | pip / uv / poetry |
| 依赖清单 | package.json | requirements.txt / pyproject.toml |
| 锁文件 | package-lock.json | uv.lock / poetry.lock / requirements.txt |
| node_modules | 每项目隔离 | venv 虚拟环境 |
| 入口脚本 | `"scripts": {...}` | `if __name__ == "__main__":` / console_scripts |
| 环境变量 | process.env | os.environ / os.getenv |
| 日志 | console + winston/pino | logging |
| CLI 参数 | yargs/commander | argparse/typer |
| tree-shaking | 支持 | 不支持（运行时导入） |

## 13.11 小练习

```python
# 1. 统计目录下各扩展名文件数量
from collections import Counter
from pathlib import Path

def count_by_suffix(root: str = ".") -> Counter:
    return Counter(p.suffix or "<none>" for p in Path(root).rglob("*") if p.is_file())

# 2. 安全的模块级单例配置
# config.py
# _settings = None
# def get_settings():
#     global _settings
#     if _settings is None:
#         _settings = load()
#     return _settings
```

- [ ] 我知道 `from math import *` 的问题。
- [ ] 我知道模块只在首次导入时执行一次。
- [ ] 我知道 `if __name__ == "__main__":` 的判断依据。
- [ ] 我知道 `json.dumps` 与 `json.dump` 的区别。
- [ ] 我能说出 venv 与 node_modules 的异同。
