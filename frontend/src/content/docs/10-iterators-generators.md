# 10 迭代器与生成器

> 主题标签：`iterators` ｜ 对应考试主题：迭代器与生成器

## 10.1 可迭代对象 vs 迭代器

```python
nums = [1, 2, 3]        # 可迭代（iterable），不是迭代器
it = iter(nums)         # 通过 __iter__ 得到迭代器
print(next(it))         # 1
print(next(it))         # 2
print(next(it))         # 3
# next(it)              # StopIteration

print(hasattr(nums, "__iter__"))    # True
print(hasattr(nums, "__next__"))    # False  ← 列表没有 __next__
print(hasattr(it, "__next__"))      # True
```

协议总结：

| 角色 | 需要实现 | 例子 |
| --- | --- | --- |
| 可迭代对象 | `__iter__`（返回迭代器） | list、dict、set、str、file、range |
| 迭代器 | `__iter__` + `__next__` | 生成器、`iter(list)`、`map/filter/zip` 对象 |

`for` 循环的本质：

```python
it = iter(iterable)
while True:
    try:
        x = next(it)
    except StopIteration:
        break
    # 处理 x
```

## 10.2 生成器函数

```python
def countdown(n: int):
    print("开始")
    while n > 0:
        yield n            # 产出并暂停
        n -= 1
    print("结束")

g = countdown(3)           # 只创建对象，不执行函数体！
print(type(g))             # <class 'generator'>
print(next(g))             # 开始 / 3
print(next(g))             # 2
print(next(g))             # 1
# next(g)                  # 结束 / StopIteration

for x in countdown(3):     # for 会自动处理 StopIteration
    print(x)
```

关键点：

- 含 `yield` 的函数调用后返回**生成器对象**，函数体不立即执行。
- 每次 `next()` 执行到下一个 `yield` 后暂停，局部变量与执行位置被保留。
- 生成器也是迭代器，因此**只能遍历一次**。

## 10.3 惰性求值的价值

```python
# 读 10GB 日志：一行一行处理，内存恒定
def read_lines(path: str):
    with open(path, encoding="utf-8") as f:
        for line in f:            # 文件对象本身也是惰性迭代器
            yield line.rstrip("\n")

# 管道式处理
lines = read_lines("app.log")
errors = (l for l in lines if "ERROR" in l)
first_ten = [next(errors, None) for _ in range(10)]
```

内存对比：

```python
import sys
print(sys.getsizeof([x for x in range(10_000)]))    # 列表：约 80KB
print(sys.getsizeof((x for x in range(10_000))))    # 生成器：约 200B
```

## 10.4 无限序列

```python
def fibonacci():
    a, b = 0, 1
    while True:
        yield a
        a, b = b, a + b

from itertools import islice
print(list(islice(fibonacci(), 10)))    # [0,1,1,2,3,5,8,13,21,34]

# 取前 n 个的一般写法
def take(n, iterable):
    return list(islice(iterable, n))
```

**千万不要**对无限生成器调用 `list()` 或 `sum()`。

## 10.5 yield from 与委托

```python
def chain(*iterables):
    for it in iterables:
        yield from it          # 等价于 for x in it: yield x

print(list(chain([1, 2], "ab", (3,))))   # [1, 2, 'a', 'b', 3]

# 递归展平嵌套列表
def flatten(items):
    for item in items:
        if isinstance(item, (list, tuple)):
            yield from flatten(item)
        else:
            yield item

print(list(flatten([1, [2, [3, [4]]]])))   # [1, 2, 3, 4]
```

## 10.6 生成器的方法：send / throw / close

```python
def echo():
    while True:
        received = yield          # yield 表达式的值来自 send
        if received is None:
            break
        print(f"收到 {received}")

g = echo()
next(g)               # 必须先启动到第一个 yield（或 g.send(None)）
g.send("hello")       # 收到 hello
g.send("world")       # 收到 world
g.close()             # 关闭生成器
```

这是协程（coroutine）的雏形，`async/await` 在底层与之相关（详见第 17 章）。

## 10.7 itertools 速查

```python
from itertools import (
    count, cycle, repeat, chain, islice, takewhile, dropwhile,
    groupby, accumulate, product, permutations, combinations, tee,
)

print(list(islice(count(10, 2), 4)))          # [10, 12, 14, 16]
print(list(takewhile(lambda x: x < 5, count())))     # [0, 1, 2, 3, 4]
print(list(accumulate([1, 2, 3, 4])))         # [1, 3, 6, 10]   前缀和
print(list(chain([1], [2, 3])))               # [1, 2, 3]
print(list(product("ab", [1, 2])))            # [('a',1),('a',2),('b',1),('b',2)]
print(list(combinations("abc", 2)))           # [('a','b'),('a','c'),('b','c')]
print(list(permutations("ab")))               # [('a','b'),('b','a')]

# groupby 需要先按 key 排序
data = [("dev", "A"), ("ops", "B"), ("dev", "C")]
for key, group in groupby(sorted(data), key=lambda kv: kv[0]):
    print(key, [x[1] for x in group])
```

## 10.8 常见陷阱

**① 生成器只能消费一次**

```python
g = (x for x in range(3))
print(list(g))     # [0, 1, 2]
print(list(g))     # []      ← 已耗尽
print(sum(g))      # 0
```

需要多次使用就物化成列表，或用 `itertools.tee`（会缓存，注意内存）。

**② 忘记惰性：调用生成器函数不会执行**

```python
def g():
    print("side effect")
    yield 1

g()          # 什么都不打印！需要 next()/for/list 驱动
```

**③ 在生成器里被 `return` 提前结束**

```python
def g():
    yield 1
    return "done"      # 触发 StopIteration，普通 for 拿不到 "done"
```

**④ 用完生成器后没有触发 finally 的清理**

```python
def gen(path):
    f = open(path)
    try:
        yield from f
    finally:
        f.close()      # 生成器被 GC 或 close() 时才执行
```

使用 `with` + 完整遍历，或显式 `g.close()`。

## 10.9 自定义迭代器类

```python
class CountDown:
    def __init__(self, start: int):
        self.current = start

    def __iter__(self):
        return self

    def __next__(self):
        if self.current <= 0:
            raise StopIteration
        self.current -= 1
        return self.current + 1

print(list(CountDown(3)))    # [3, 2, 1]
```

## 10.10 与 JS/TS 对照

| 需求 | TypeScript | Python |
| --- | --- | --- |
| 生成器函数 | `function* g() { yield 1 }` | `def g(): yield 1` |
| 取值 | `g.next().value` | `next(g)` |
| 结束信号 | `{done: true}` | `StopIteration` 异常 |
| 委托 | `yield* other` | `yield from other` |
| 惰性映射 | 生成器函数 | 生成器表达式 |
| 无限序列 | `while(true) yield i++` | `itertools.count()` |
| 一次消费 | 是 | 是 |
| 异步生成器 | `async function*` | `async def` + `async for` |

## 10.11 小练习

```python
# 1. 分批读取（批处理常用）
def chunks(iterable, size: int):
    batch = []
    for item in iterable:
        batch.append(item)
        if len(batch) == size:
            yield batch
            batch = []
    if batch:
        yield batch

print(list(chunks(range(7), 3)))   # [[0,1,2],[3,4,5],[6]]

# 2. 滑动窗口
def windows(seq, size: int):
    for i in range(len(seq) - size + 1):
        yield seq[i:i + size]

print(list(windows([1, 2, 3, 4], 2)))   # [[1,2],[2,3],[3,4]]
```

- [ ] 我能说出 iterable 与 iterator 的区别。
- [ ] 我知道调用生成器函数不会执行函数体。
- [ ] 我知道生成器只能遍历一次。
- [ ] 我知道大文件要逐行迭代而不是 `read()`。
