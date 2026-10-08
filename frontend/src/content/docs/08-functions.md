# 08 函数与作用域

> 主题标签：`functions` ｜ 对应考试主题：函数与作用域

## 8.1 定义与调用

```python
def greet(name: str) -> str:
    """返回问候语。"""
    return f"Hello, {name}!"

print(greet("Alice"))     # Hello, Alice!
print(greet)              # <function greet at 0x...>  函数本身是对象
```

- `def 名字(参数):` + 缩进函数体。
- 没有 `return` 时返回 `None`。
- 函数是**一等对象**：可赋值、可作为参数、可作为返回值（与 JS 一致）。

```python
def apply(fn, value):
    return fn(value)

print(apply(lambda x: x * 2, 21))   # 42

handlers = {"add": lambda a, b: a + b}
print(handlers["add"](1, 2))        # 3
```

## 8.2 参数的五种形态

```python
def f(a, b=2, *args, c, d=4, **kwargs):
    """
    a        位置参数（必填）
    b        默认参数（可省略）
    *args    收集多余的位置参数 -> tuple
    c        仅关键字参数（必须写 c=...）
    d        仅关键字参数（有默认值）
    **kwargs 收集多余的关键字参数 -> dict
    """
    print(a, b, args, c, d, kwargs)

f(1, 3, 5, 6, c=7, e=9)   # 1 3 (5, 6) 7 4 {'e': 9}
```

调用时的解包：

```python
nums = [1, 2, 3]
print(*nums)                # 等价 print(1, 2, 3)
opts = {"sep": "-"}
print("a", "b", **opts)     # a-b
```

> 记忆点：`*args` 是 **tuple**，`**kwargs` 是 **dict**；定义处是“收集”，调用处是“展开”。

### 参数顺序铁律

```
位置参数 → 默认参数 → *args → 仅关键字参数 → **kwargs
```

违反会 `SyntaxError`：

```python
def bad(a=1, b): ...      # ❌ 非默认参数不能跟在默认参数后
def bad2(*args, a, a2): ...  # 合法
def f(b=2, 1): ...        # ❌ 调用时位置参数必须在关键字参数前
```

## 8.3 默认参数陷阱（必考）

```python
def add_item(item, bag=[]):     # ❌ 可变默认值
    bag.append(item)
    return bag

print(add_item("a"))    # ['a']
print(add_item("b"))    # ['a', 'b']  ← 居然记住了上次的结果！
```

原因：默认值在 **def 执行时**求值一次并保存在函数对象里（`add_item.__defaults__`）。

正确写法：

```python
def add_item(item, bag=None):
    if bag is None:
        bag = []
    bag.append(item)
    return bag
```

其他正确姿势：

```python
def f(x, cache={}):        # ✅ 有意为之的缓存（记忆化）
    return cache.setdefault(x, x * 2)
```

## 8.4 参数传递：对象引用

```python
def modify(lst):
    lst.append(1)      # 原地修改 -> 影响调用者

def rebind(lst):
    lst = [9, 9]       # 只改本地名字 -> 不影响调用者

a = [0]
modify(a); print(a)    # [0, 1]
rebind(a); print(a)    # [0, 1]
```

- 传的是“对象引用的副本”，既不是纯值传递，也不是 C 的指针。
- 不可变对象（int/str/tuple）无法原地修改，因此看起来像值传递。
- 想避免被修改：传入副本 `f(lst.copy())`，或在函数内部 `copy.deepcopy`。

## 8.5 作用域规则 LEGB

查找顺序：**L**ocal → **E**nclosing → **G**lobal → **B**uilt-in

```python
x = "global"

def outer():
    x = "enclosing"
    def inner():
        # x = "local"      # 有赋值语句时 x 就是 local
        return x
    return inner()

print(outer())     # enclosing
print(x)           # global（函数内赋值不影响全局）
```

赋值会让名字变成局部变量，因此：

```python
count = 0

def inc():
    count += 1        # ❌ UnboundLocalError：把 count 当成了局部变量

def inc_ok():
    global count      # ✅ 声明使用全局变量
    count += 1

def outer():
    n = 0
    def inner():
        nonlocal n    # ✅ 修改外层函数的变量
        n += 1
    inner()
    return n
```

> 与 JS 对比：Python **没有** `var/let` 的块级作用域，但函数内的赋值确实创建局部变量；`nonlocal` 相当于“修改闭包变量”。

## 8.6 闭包与延迟绑定

```python
def make_counter():
    count = 0
    def counter():
        nonlocal count
        count += 1
        return count
    return counter

c = make_counter()
print(c(), c(), c())    # 1 2 3
```

循环变量陷阱：

```python
funcs = [lambda: i for i in range(3)]
print([f() for f in funcs])       # [2, 2, 2]  ← 闭包捕获的是变量 i

funcs = [lambda i=i: i for i in range(3)]
print([f() for f in funcs])       # [0, 1, 2]  ← 用默认参数冻结当前值
```

## 8.7 返回值

```python
def divmod2(a, b):
    return a // b, a % b     # 实际返回一个元组

q, r = divmod2(7, 2)
print(q, r)                  # 3 1

def maybe(x):
    if x < 0:
        return None          # 显式返回 None 更清楚
    return x * 2
```

- 多返回值 = 元组打包 + 解包。
- 提前返回（early return）能让代码更扁平，比深层嵌套更好读。

## 8.8 lambda

```python
square = lambda x: x * x          # 等价 def square(x): return x * x
pairs = [(1, "b"), (2, "a")]
pairs.sort(key=lambda p: p[1])    # 作为 key 函数最常见

# 限制：只能写单个表达式，不能有语句/注解/多行
```

能用 `def` 就优先用 `def`（可读性、可调试、可加文档），`lambda` 只在“短小的 key/回调”里使用。

## 8.9 类型注解与文档

```python
from typing import Iterable

def mean(values: Iterable[float]) -> float:
    """求平均值。

    Args:
        values: 可迭代的数字序列。

    Returns:
        平均值；空序列返回 0.0。

    Raises:
        TypeError: values 含非数字时由 sum 抛出。
    """
    values = list(values)
    if not values:
        return 0.0
    return sum(values) / len(values)
```

注解**运行时不检查**（需要 mypy/pyright 或 Pydantic 等库）。详见第 15 章。

## 8.10 函数工具（functools）

```python
from functools import lru_cache, partial, reduce, wraps

@lru_cache(maxsize=None)     # 记忆化缓存（参数必须可哈希）
def fib(n: int) -> int:
    return n if n < 2 else fib(n - 1) + fib(n - 2)

print(fib(50))               # 极快

add = lambda a, b: a + b
add5 = partial(add, 5)       # 预填第一个参数
print(add5(3))               # 8

from functools import reduce
print(reduce(lambda acc, x: acc + x, [1, 2, 3], 0))   # 6
```

## 8.11 与 JS/TS 对照

| 需求 | TypeScript | Python |
| --- | --- | --- |
| 定义函数 | `function f(a: number) {}` | `def f(a: int) -> None:` |
| 箭头函数 | `(x) => x * 2` | `lambda x: x * 2` |
| 默认参数 | `function f(a = 1) {}` | `def f(a=1):` |
| 剩余参数 | `(...args: number[])` | `*args`（tuple） |
| 命名可选参数 | 对象解构 `{a, b}` | 关键字参数 `def f(a, b)` |
| 多返回值 | 返回对象/数组 | 返回元组，调用处解包 |
| 函数提升 | 声明会提升 | 没有提升，必须先定义 |
| 闭包变量修改 | 直接修改 | 需要 `nonlocal` |
| 模块级变量修改 | 闭包/模块作用域 | 需要 `global` |
| 函数重载 | TS 支持重载签名 | 用默认参数、`*args`、`functools.singledispatch` |

## 8.12 小练习

```python
# 1. 修复可变默认参数
def collect(items=None):
    items = [] if items is None else items
    items.append("x")
    return items

# 2. 可变参数求平均
def avg(*nums: float) -> float:
    return sum(nums) / len(nums) if nums else 0.0

# 3. 仅关键字参数提升可读性
def transfer(from_acct, to_acct, *, amount: float, note: str = "") -> None:
    ...

# transfer("A", "B", 100)              # TypeError，必须写 amount=100
transfer("A", "B", amount=100)
```

- [ ] 我能说出 `*args` 与 `**kwargs` 的类型。
- [ ] 我能解释可变默认参数为什么会“记住”上次结果。
- [ ] 我知道 `global` 与 `nonlocal` 的区别。
- [ ] 我知道函数内 `lst.append(x)` 会影响调用者，而 `lst = [...]` 不会。
