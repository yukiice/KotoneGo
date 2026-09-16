# 09 推导式（Comprehensions）

> 主题标签：`comprehensions` ｜ 对应考试主题：推导式

## 9.1 四种推导式与生成器表达式

```python
# 列表推导式 list
squares = [x * x for x in range(5)]              # [0, 1, 4, 9, 16]

# 集合推导式 set
mods = {x % 3 for x in range(10)}                # {0, 1, 2}

# 字典推导式 dict
index = {name: i for i, name in enumerate(["a", "b"])}   # {'a': 0, 'b': 1}

# 生成器表达式 generator（惰性、只能遍历一次）
gen = (x * x for x in range(5))
print(sum(gen))                                  # 30
print(list(gen))                                 # []   ← 已经耗尽了
```

## 9.2 基本语法结构

```
[表达式 for 变量 in 可迭代对象 if 条件]
```

“表达式”是**映射**，“if 条件”是**过滤**：

```python
prices = [100, 20, 300]
print([p * 0.8 for p in prices])              # 打折
print([p for p in prices if p > 50])          # 过滤
print([p * 0.8 for p in prices if p > 50])    # 先过滤再映射
```

条件表达式（三元）写在前面的表达式位置：

```python
print([p if p > 50 else 0 for p in prices])   # [100, 0, 300]
```

**注意区别**：

```python
[x for x in nums if x > 0]            # ✅ 过滤
[x if x > 0 else 0 for x in nums]     # ✅ 映射 + 兜底
[x for x in nums if x > 0 else 0]     # ❌ SyntaxError
```

## 9.3 多重 for 与嵌套

```python
pairs = [(x, y) for x in range(2) for y in range(2)]
# [(0,0), (0,1), (1,0), (1,1)]

matrix = [[1, 2], [3, 4]]
flat = [n for row in matrix for n in row]        # [1, 2, 3, 4]
transposed = [[row[i] for row in matrix] for i in range(2)]   # [[1, 3], [2, 4]]

# 等价的多重 for 循环
result = []
for x in range(2):
    for y in range(2):
        result.append((x, y))
```

嵌套推导式构建二维结构（比 `[[0]*n]*m` 安全）：

```python
grid = [[0] * 3 for _ in range(2)]
grid[0][0] = 1
print(grid)          # [[1, 0, 0], [0, 0, 0]]  ← 只有第一行变了
```

## 9.4 作用域

```python
x = "outer"
values = [x for x in range(3)]
print(values)     # [0, 1, 2]
print(x)          # 'outer'   ← 推导式的 x 不会泄漏（Python 3）
```

推导式内部是独立作用域（Python 3 起），与 `for` 循环会泄漏变量不同。

## 9.5 什么时候不该用推导式

```python
# ❌ 逻辑复杂、有副作用：难读
[log(i) for i in items if validate(i) or (fix(i) and retry(i))]

# ✅ 用普通循环
for i in items:
    if validate(i):
        log(i)
    elif fix(i):
        retry(i)
        log(i)
```

判断标准：

- 只做“映射/过滤/生成新序列” → 推导式。
- 有副作用（I/O、打印、写库）→ 普通循环。
- 嵌套超过两层 → 拆函数或普通循环。
- 需要调试中间过程 → 普通循环。

## 9.6 性能与内存

```python
import sys, timeit

n = 100_000
print(sys.getsizeof([x for x in range(1000)]))   # ~8KB+ 列表本体
print(sys.getsizeof(x for x in range(1000)))     # ~200B  生成器

# 推导式通常比 for + append 快（C 层循环），也比 map+lambda 清晰
timeit.timeit("[x*2 for x in range(1000)]", number=1000)
```

选择建议：

| 场景 | 用哪个 |
| --- | --- |
| 需要多次遍历、索引、len | 列表推导式 |
| 一次性消费（sum/max/join/any/all） | 生成器表达式 |
| 需要去重 | 集合推导式 |
| 构造映射 | 字典推导式 |
| 数据量极大、内存受限 | 生成器表达式 |

## 9.7 常用组合技

```python
from pathlib import Path

# 1. 展平一层
flat = [x for row in rows for x in row]

# 2. 字典反转
flipped = {v: k for k, v in mapping.items()}

# 3. 过滤 + 归一化
clean = [s.strip().lower() for s in lines if s.strip()]

# 4. 条件计数
positive = sum(1 for n in nums if n > 0)

# 5. 任意/全部满足
has_error = any("ERROR" in line for line in lines)
all_ok = all(x > 0 for x in nums)

# 6. 列表转字典
by_id = {item["id"]: item for item in items}

# 7. 分组（配合 defaultdict 更清晰）
grouped = {dept: [p for p in people if p["dept"] == dept] for dept in {p["dept"] for p in people}}

# 8. 读取文件里的非空行
lines = [line.strip() for line in Path("a.txt").read_text(encoding="utf-8").splitlines() if line.strip()]

# 9. 生成器做管道
env = (line for line in Path(".env").read_text().splitlines())
pairs = (line.split("=", 1) for line in env if line and not line.startswith("#"))
config = {k.strip(): v.strip() for k, v in pairs}
```

## 9.8 与 JS/TS 对照

| 需求 | TypeScript | Python |
| --- | --- | --- |
| map | `arr.map(x => x * 2)` | `[x * 2 for x in arr]` |
| filter | `arr.filter(x => x > 0)` | `[x for x in arr if x > 0]` |
| map + filter | `arr.filter(x => x > 0).map(x => x * 2)` | `[x * 2 for x in arr if x > 0]` |
| flatMap | `arr.flatMap(x => x)` | `[y for x in arr for y in x]` |
| Set | `new Set(arr)` | `{x for x in arr}` |
| Object.fromEntries | `Object.fromEntries(arr.map(...))` | `{k: v for k, v in arr}` |
| 惰性序列 | 生成器函数 / RxJS | 生成器表达式 `(x for x in ...)` |
| 无限序列 | 手写迭代器 | `itertools.count()` |

## 9.9 小练习

```python
# 1. 提取所有偶数的平方
print([n ** 2 for n in range(20) if n % 2 == 0])

# 2. 转置矩阵
m = [[1, 2, 3], [4, 5, 6]]
print([list(col) for col in zip(*m)])     # [[1, 4], [2, 5], [3, 6]]

# 3. 词频 Top3
from collections import Counter
text = "the quick brown fox the lazy dog the"
print(Counter(text.split()).most_common(3))

# 4. 用生成器求文件中最长的行
longest = max((len(line) for line in open("a.txt", encoding="utf-8")), default=0)
```

- [ ] 我能区分过滤 `if` 与条件表达式 `x if c else y` 的位置。
- [ ] 我知道生成器表达式只能遍历一次。
- [ ] 我知道 `[x for x in ...]` 里的变量不会泄漏。
- [ ] 我知道有副作用时应该用普通循环。
