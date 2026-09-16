# 16 闭包与装饰器

> 主题标签：`decorators` ｜ 对应考试主题：闭包与装饰器
> 装饰器 ≈ React 的 HOC（高阶组件）在函数层面的对应物。

## 16.1 函数是一等对象

```python
def shout(text: str) -> str:
    return text.upper()

f = shout               # 不加括号：引用函数对象
print(f("hi"))          # HI
print(shout is f)       # True

def apply(fn, value):   # 函数作为参数（高阶函数）
    return fn(value)

print(apply(shout, "hi"))         # HI
print(sorted(["bb", "a"], key=len))   # 函数作为配置
```

关键区别：`fn` 是对象，`fn()` 是调用。

## 16.2 闭包

```python
def make_multiplier(factor: int):
    def multiply(x: int) -> int:
        return x * factor          # 捕获外层变量 factor
    return multiply

double = make_multiplier(2)
triple = make_multiplier(3)
print(double(5), triple(5))        # 10 15
print(double.__closure__[0].cell_contents)   # 2
```

闭包三要素：

1. 内层函数；
2. 内层函数引用了外层函数的变量（自由变量）；
3. 外层函数返回内层函数。

修改被捕获的变量要用 `nonlocal`：

```python
def counter():
    n = 0
    def inc():
        nonlocal n
        n += 1
        return n
    return inc

c = counter()
print(c(), c(), c())     # 1 2 3
```

**延迟绑定陷阱**：

```python
fs = [lambda: i for i in range(3)]
print([f() for f in fs])         # [2, 2, 2]  ← 都捕获同一个变量

fs = [lambda i=i: i for i in range(3)]
print([f() for f in fs])         # [0, 1, 2]  ← 默认参数在定义时求值
```

## 16.3 最简装饰器

```python
import time
from functools import wraps

def timer(func):
    @wraps(func)                       # 保留 __name__/__doc__
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        try:
            return func(*args, **kwargs)
        finally:
            cost = time.perf_counter() - start
            print(f"{func.__name__} 耗时 {cost:.4f}s")
    return wrapper

@timer
def slow(n: int) -> int:
    """模拟耗时计算。"""
    return sum(range(n))

slow(1_000_000)
print(slow.__name__)      # slow（没有 wraps 会变成 wrapper）
print(slow.__doc__)       # 模拟耗时计算。
```

**语法糖展开**：

```python
@timer
def slow(): ...

# 完全等价于
def slow(): ...
slow = timer(slow)
```

## 16.4 带参数的装饰器

需要**三层**（或者用 `functools.partial`）：

```python
def retry(times: int = 3, delay: float = 0.5, exceptions=(Exception,)):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exc = None
            for attempt in range(1, times + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as exc:
                    last_exc = exc
                    print(f"{func.__name__} 第 {attempt} 次失败：{exc}")
                    if attempt < times:
                        time.sleep(delay)
            raise last_exc
        return wrapper
    return decorator

@retry(times=3, delay=0.1)
def flaky() -> str:
    ...
```

调用链：`@retry(times=3)` → 先执行 `retry(3)` 得到 `decorator` → 再 `flaky = decorator(flaky)`。

## 16.5 装饰器叠加顺序

```python
@a
@b
def f(): ...

# 等价于 f = a(b(f))：**下面的先应用**

# 但执行（进入）顺序是 a 的 wrapper 先跑，再 b 的 wrapper：
# a.before -> b.before -> f -> b.after -> a.after
```

```python
def tag(name):
    def deco(func):
        @wraps(func)
        def wrapper(*a, **kw):
            return f"<{name}>{func(*a, **kw)}</{name}>"
        return wrapper
    return deco

@tag("outer")
@tag("inner")
def hello():
    return "hi"

print(hello())     # <outer><inner>hi</inner></outer>
```

## 16.6 类装饰器与应用注册表

```python
# 1) 给类注入方法
def add_repr(cls):
    def __repr__(self):
        return f"{cls.__name__}({self.__dict__})"
    cls.__repr__ = __repr__
    return cls

@add_repr
class Point:
    def __init__(self, x, y):
        self.x, self.y = x, y

print(Point(1, 2))     # Point({'x': 1, 'y': 2})

# 2) 注册表模式（插件/命令行命令常用）
REGISTRY: dict[str, object] = {}

def register(name: str):
    def deco(func):
        REGISTRY[name] = func
        return func
    return deco

@register("hello")
def cmd_hello():
    print("hello")

print(REGISTRY)        # {'hello': <function cmd_hello ...>}
```

`@dataclass` 就是“接收类 → 修改并返回类”的装饰器。

## 16.7 functools 三个好帮手

```python
from functools import lru_cache, partial, wraps

@lru_cache(maxsize=128)      # 记忆化：相同参数直接返回缓存（参数需可哈希）
def fib(n: int) -> int:
    return n if n < 2 else fib(n - 1) + fib(n - 2)

print(fib(100))              # 立刻返回
print(fib.cache_info())      # CacheInfo(hits=98, misses=101, ...)

def power(base: float, exp: float) -> float:
    return base ** exp

square = partial(power, exp=2)      # 预填参数
print(square(5))                    # 25.0
```

`singledispatch`：按类型分派（类似函数重载）：

```python
from functools import singledispatch

@singledispatch
def describe(value) -> str:
    return f"未知类型：{type(value).__name__}"

@describe.register
def _(value: int) -> str:
    return f"整数 {value}"

@describe.register
def _(value: list) -> str:
    return f"列表，共 {len(value)} 项"

print(describe(1), describe([1, 2]), describe(1.5))
```

## 16.8 类型友好的装饰器（ParamSpec）

```python
from typing import ParamSpec, TypeVar, Callable
from functools import wraps

P = ParamSpec("P")
R = TypeVar("R")

def logged(func: Callable[P, R]) -> Callable[P, R]:
    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        print(f"调用 {func.__name__}")
        return func(*args, **kwargs)
    return wrapper

@logged
def add(a: int, b: int) -> int:
    return a + b

reveal = add(1, 2)      # mypy 仍知道签名是 (int, int) -> int
```

`functools.wraps` 只复制运行时元数据，`ParamSpec` 才让类型检查器保留签名。

## 16.9 异步装饰器

```python
import asyncio
from functools import wraps
from typing import Awaitable, Callable, TypeVar

R = TypeVar("R")

def async_timer(func: Callable[..., Awaitable[R]]) -> Callable[..., Awaitable[R]]:
    @wraps(func)
    async def wrapper(*args, **kwargs) -> R:
        start = asyncio.get_event_loop().time()
        result = await func(*args, **kwargs)
        print(f"{func.__name__} 耗时 {asyncio.get_event_loop().time() - start:.3f}s")
        return result
    return wrapper

@async_timer
async def fetch() -> str:
    await asyncio.sleep(0.1)
    return "done"
```

## 16.10 常见错误

| 错误 | 症状 | 修复 |
| --- | --- | --- |
| 忘记返回内层函数 | 装饰后 `f` 变成 `None` | `return wrapper` |
| 不写 `wraps` | `__name__` 变成 `wrapper`，调试困难 | 加 `@wraps(func)` |
| 忘记 `*args, **kwargs` | 被装饰函数带参数时报 TypeError | 透传参数 |
| 把方法装饰后用 `self` | 描述符失效（少见） | 用 `self` 正常传参即可 |
| 装饰器里吞异常 | 错误被隐藏 | 记录 + 重抛 |
| 循环/递归中使用 lru_cache 无上限 | 内存增长 | 设置 `maxsize` |

## 16.11 与前端概念对照

| 前端概念 | Python 对应 |
| --- | --- |
| 高阶组件 HOC | 接收类/函数并返回新的装饰器 |
| 中间件（Express/Koa） | 装饰器链（洋葱模型） |
| `useMemo` / `useCallback` | `functools.lru_cache` |
| 依赖注入容器 | 带参装饰器 + 注册表 |
| Proxy / 代理对象 | `wrapper` 包装调用 |
| `bind` | `functools.partial` |

## 16.12 小练习

```python
# 1. 限流装饰器
def rate_limit(max_calls: int, period: float):
    def deco(func):
        calls: list[float] = []
        @wraps(func)
        def wrapper(*args, **kwargs):
            now = time.monotonic()
            calls[:] = [t for t in calls if now - t < period]
            if len(calls) >= max_calls:
                raise RuntimeError("调用过于频繁")
            calls.append(now)
            return func(*args, **kwargs)
        return wrapper
    return deco

# 2. 参数校验装饰器
def require_positive(*names):
    def deco(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            bound = inspect.signature(func).bind(*args, **kwargs)
            for name in names:
                if bound.arguments.get(name, 0) <= 0:
                    raise ValueError(f"{name} 必须为正数")
            return func(*args, **kwargs)
        return wrapper
    return deco
```

- [ ] 我知道 `@deco` 等价于 `f = deco(f)`。
- [ ] 我知道装饰器为什么需要 `@wraps`。
- [ ] 我知道带参装饰器为什么要三层函数。
- [ ] 我知道多个装饰器的应用顺序与执行顺序。
- [ ] 我能解释循环里 lambda 捕获同一变量的原因与修复方法。
