# 15 类型注解与 mypy

> 主题标签：`typing` ｜ 对应考试主题：类型注解与 mypy
> 对前端读者来说，这一章等价于“把 TypeScript 的类型能力接到 Python 上”。

## 15.1 注解不参与运行时

```python
def add(a: int, b: int) -> int:
    return a + b

print(add("1", "2"))        # '12'  ← 不报错！注解只是元数据
print(add.__annotations__)  # {'a': <class 'int'>, 'b': <class 'int'>, 'return': <class 'int'>}
```

要点：

- 注解**不做运行时校验**，也不做类型转换。
- 想要静态检查：`mypy` / `pyright`（相当于 `tsc`）。
- 想要运行期校验：Pydantic、`typeguard`、`beartype`。

## 15.2 基础写法

```python
from typing import Any

name: str = "Alice"
count: int
ratio: float = 0.5
flag: bool = True
items: list[str] = []
mapping: dict[str, int] = {}
pair: tuple[int, str] = (1, "a")
point: tuple[float, float] = (1.0, 2.0)
numbers: set[int] = set()
anything: Any = object()          # 关闭类型检查（慎用）

def greet(name: str, times: int = 1) -> str:
    return f"hi {name} " * times

def log(msg: str) -> None:        # 无返回值（只做副作用）
    print(msg)

def parse(text: str) -> int | None:      # 可能失败返回 None
    try:
        return int(text)
    except ValueError:
        return None
```

Python 3.9+ 可以直接用内置容器做泛型（`list[str]`），老代码用 `typing.List[str]`。

## 15.3 Optional / Union / 联合类型

```python
from typing import Optional, Union

def f1(x: Optional[str]) -> None: ...          # 老写法
def f2(x: str | None) -> None: ...             # 3.10+ 推荐
def f3(x: int | str | float) -> str: ...       # 联合类型
def f4(x: Union[int, str]) -> None: ...        # 老写法
```

严格模式下 `def f(x: str = None)` 会报错（默认值类型不匹配），要写 `x: str | None = None`。

## 15.4 容器与泛型

```python
from collections.abc import Iterable, Iterator, Sequence, Mapping, Callable

def total(nums: Iterable[int]) -> int:
    return sum(nums)

def first(items: Sequence[str]) -> str | None:
    return items[0] if items else None

def transform(xs: list[int], fn: Callable[[int], str]) -> list[str]:
    return [fn(x) for x in xs]

def index_by(rows: list[dict[str, Any]], key: str) -> dict[str, dict[str, Any]]:
    return {row[key]: row for row in rows}
```

**参数类型该宽还是该窄**：入参用抽象类型（`Iterable`/`Sequence`/`Mapping`），返回值用具体类型（`list`/`dict`），这叫“参数逆变、返回协变”的实用原则。

## 15.5 TypeVar：泛型

```python
from typing import TypeVar
T = TypeVar("T")

def first_or(items: list[T], default: T) -> T:
    return items[0] if items else default

n = first_or([1, 2], 0)        # mypy 推断 n: int
s = first_or(["a"], "b")       # s: str
```

约束与绑定：

```python
Number = TypeVar("Number", int, float)          # 只能是 int 或 float
Comparable = TypeVar("Comparable", bound="Base") # 必须是 Base 的子类
```

Python 3.12+ 新语法：

```python
def first_or[T](items: list[T], default: T) -> T: ...
class Stack[T]: ...
type Point = tuple[float, float]                 # 类型别名
```

## 15.6 TypedDict / NamedTuple / dataclass

```python
from typing import TypedDict, NotRequired

class UserDict(TypedDict):
    id: int
    name: str
    email: NotRequired[str]        # 可选键

u: UserDict = {"id": 1, "name": "Alice"}   # 运行时就是普通 dict

from typing import NamedTuple
class Point(NamedTuple):
    x: float
    y: float

from dataclasses import dataclass
@dataclass(frozen=True)
class Config:
    host: str = "localhost"
    port: int = 8000
```

选择建议：

| 需求 | 用什么 |
| --- | --- |
| 描述 JSON / 外部 dict 结构 | `TypedDict` |
| 轻量不可变元组 | `NamedTuple` |
| 有方法的对象、需要默认值/校验 | `dataclass` |
| 运行时校验 + 序列化（API 层） | Pydantic `BaseModel` |

## 15.7 Literal / Final / Annotated

```python
from typing import Literal, Final, Annotated

Mode = Literal["r", "w", "a"]         # 只能是这几个字面量之一
def open_file(path: str, mode: Mode = "r") -> None: ...

MAX_RETRY: Final = 3                   # 不允许再赋值（静态检查）
Token = Annotated[str, "JWT"]          # 附加元数据（Pydantic/FastAPI 常用）
```

## 15.8 前向引用与循环依赖

```python
# 类内部引用自身
class Node:
    def __init__(self, value: int, next: "Node | None" = None):
        self.value = value
        self.next = next

# 全局开启延迟求值（3.7+ 写法，未来会成为默认）
from __future__ import annotations

class Tree:
    def add(self, child: Tree) -> None: ...   # 不用加引号了
```

```python
# 只用于类型检查的导入，避免循环导入
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .models import User

def handle(user: "User") -> None: ...
```

## 15.9 运行期校验：Pydantic（API 层标配）

```python
from pydantic import BaseModel, Field, field_validator

class CreateUser(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    age: int = Field(ge=0, le=150)
    email: str | None = None

    @field_validator("name")
    @classmethod
    def strip_name(cls, v: str) -> str:
        return v.strip()

u = CreateUser(name=" Alice ", age=30)
print(u.model_dump())      # {'name': 'Alice', 'age': 30, 'email': None}

try:
    CreateUser(name="", age=-1)
except Exception as exc:
    print("校验失败", exc)
```

> 本项目的后端就是 FastAPI + Pydantic：请求体自动校验，类型注解直接驱动接口文档（`/docs`）。

## 15.10 mypy 配置与实践

```toml
# pyproject.toml
[tool.mypy]
python_version = "3.11"
strict = true
warn_unused_ignores = true
warn_unreachable = true
disallow_untyped_defs = true

[[tool.mypy.overrides]]
module = ["third_party_lib.*"]
ignore_missing_imports = true
```

```bash
mypy .                     # 检查整个项目
mypy app/main.py           # 检查单文件
mypy --strict app
```

常用逃逸手段（尽量少用）：

```python
x: Any = something_dynamic()
value = cast(str, obj)             # 断言类型（无运行时开销）
# type: ignore[arg-type]           # 忽略某行的特定错误
assert isinstance(obj, str)         # 收窄类型（也真的会校验）
```

## 15.11 与 TS 对照表

| TypeScript | Python |
| --- | --- |
| `x: number` | `x: int` / `x: float` |
| `x?: string` | `x: str \| None = None` |
| `string \| number` | `str \| int` |
| `T[]` / `Array<T>` | `list[T]` |
| `Record<string, number>` | `dict[str, int]` |
| `[number, string]` | `tuple[int, str]` |
| `Set<T>` | `set[T]` |
| `(a: number) => string` | `Callable[[int], str]` |
| `interface` | `TypedDict` / `Protocol` / `dataclass` |
| `type X = ...` | `type X = ...`（3.12+）/ `X = ...` |
| `any` | `Any` |
| `unknown` | `object`（更严格） |
| `never` | `NoReturn` / `Never` |
| `as` 断言 | `cast(...)` |
| `readonly` | `Final`、`frozen=True` |
| `enum` | `enum.Enum` / `Literal` |
| 泛型 `<T>` | `TypeVar("T")` / `def f[T]` |
| 编译期检查 | `mypy` / `pyright`（独立工具） |

## 15.12 实践建议

1. **新项目直接开 `strict`**：和 TS 一样，越早越省事。
2. **公共 API 必须注解**：库、服务接口、数据模型。
3. **别用 `Any` 逃避**：优先 `object` + `isinstance` 收窄。
4. **用 `--strict` 检查，用 ruff 格式化**，把二者接进 CI 与 pre-commit。
5. **数据模型统一用 Pydantic/dataclass**，不要传裸 dict（除非是 JSON 边界且有 TypedDict）。

## 15.13 小练习

```python
from typing import TypeVar, Iterable
from dataclasses import dataclass

T = TypeVar("T")

def chunked(items: Iterable[T], size: int) -> list[list[T]]:
    """把可迭代对象切成固定大小的块。"""
    batch: list[T] = []
    result: list[list[T]] = []
    for item in items:
        batch.append(item)
        if len(batch) == size:
            result.append(batch)
            batch = []
    if batch:
        result.append(batch)
    return result

@dataclass(frozen=True)
class QuizResult:
    score: int
    total: int

    @property
    def percent(self) -> float:
        return self.score / self.total * 100 if self.total else 0.0
```

- [ ] 我知道注解在运行时不做校验。
- [ ] 我知道 `Optional[str]` 与 `str | None` 等价。
- [ ] 我能说出入参用 `Iterable`、返回用 `list` 的理由。
- [ ] 我知道 TypedDict / NamedTuple / dataclass / Pydantic 的适用场景。
- [ ] 我知道 `from __future__ import annotations` 解决的问题。
