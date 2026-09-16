# 18 易错点与 JS/TS 迁移指南

> 主题标签：`pitfalls` ｜ 对应考试主题：易错点与 JS/TS 对比

## 18.1 十大必踩坑（每一条都对应考试题）

### ① 可变默认参数

```python
def f(items=[]):        # ❌ 定义时只创建一次，跨调用共享
    items.append(1)
    return items

print(f(), f())          # [1] [1, 1]

def f(items=None):       # ✅
    items = [] if items is None else items
    items.append(1)
    return items
```

### ② `[[0] * 2] * 3` 共享内层列表

```python
bad = [[0] * 2] * 3
bad[0][0] = 1
print(bad)      # [[1,0],[1,0],[1,0]]

good = [[0] * 2 for _ in range(3)]
good[0][0] = 1
print(good)     # [[1,0],[0,0],[0,0]]
```

### ③ `list.sort()` 返回 None

```python
a = [3, 1]
b = a.sort()        # b 是 None！
c = sorted(a)       # ✅ 新列表
```

同类：`list.append`、`list.reverse`、`dict.update`、`set.add` 都返回 `None`（原地修改）。

### ④ 赋值不是复制

```python
a = [1, 2]
b = a               # 同一个对象
b.append(3); print(a)     # [1, 2, 3]

c = a.copy()        # 浅拷贝
import copy
d = copy.deepcopy(a)      # 深拷贝
```

### ⑤ `is` 与 `==`

```python
print([] == [])      # True    值相等
print([] is [])      # False   不同对象
print(None is None)  # True    单例
```

规则：`is` 只用于 `None`、`True`、`False`、哨兵对象。

### ⑥ 字符串不可变

```python
s = "abc"
# s[0] = "x"        # ❌ TypeError
s = "x" + s[1:]     # ✅

# 循环拼接慢
out = "".join(parts)   # ✅
```

### ⑦ 整除与取模的方向

```python
print(-7 // 2)   # -4（向下取整，不是 -3）
print(-7 % 3)    # 2（符号跟除数）
print(7 / 2)     # 3.5（/ 永远得 float）
```

### ⑧ 浮点精度

```python
print(0.1 + 0.2 == 0.3)                 # False
import math
print(math.isclose(0.1 + 0.2, 0.3))     # True
from decimal import Decimal
print(Decimal("0.1") + Decimal("0.2") == Decimal("0.3"))   # True
```

### ⑨ 循环里修改集合

```python
nums = [1, 2, 3, 4]
for n in nums[:]:          # ✅ 迭代副本
    if n % 2 == 0:
        nums.remove(n)

nums = [n for n in nums if n % 2 != 0]     # ✅ 或重建
```

### ⑩ 闭包延迟绑定

```python
fs = [lambda: i for i in range(3)]
print([f() for f in fs])          # [2, 2, 2]
fs = [lambda i=i: i for i in range(3)]
print([f() for f in fs])          # [0, 1, 2]
```

## 18.2 空值模型对比

| 场景 | JS/TS | Python |
| --- | --- | --- |
| 空值 | `null` / `undefined` | `None` |
| 未定义变量 | `undefined` | `NameError` |
| 属性不存在 | `undefined` | `AttributeError` |
| 键不存在 | `undefined` | `KeyError` |
| 下标越界 | `undefined` | `IndexError` |
| 数字非法 | `NaN` | `ValueError` |
| 除零 | `Infinity` | `ZeroDivisionError` |
| 可选链 | `a?.b?.c` | `getattr(a, "b", None)`，dict 用 `a.get("b", {}).get("c")` |
| 空值合并 | `a ?? b` | `a if a is not None else b` |

**核心差异**：JS 用“特殊值”表示失败，Python 用**异常**。因此 Python 代码里到处是 `try/except` 或在边界处显式转换。

```python
# 安全访问嵌套字典
def dig(data: dict, *keys, default=None):
    for k in keys:
        if isinstance(data, dict) and k in data:
            data = data[k]
        else:
            return default
    return data

print(dig({"a": {"b": 1}}, "a", "b"))     # 1
print(dig({}, "a", "b", default="?"))     # ?
```

## 18.3 真值判断差异

| 值 | JS 真值 | Python 真值 |
| --- | --- | --- |
| `0` | falsy | falsy |
| `""` | falsy | falsy |
| `"0"` | truthy | truthy |
| `[]` | **truthy** | falsy |
| `{}` | **truthy** | falsy |
| `null`/`None` | falsy | falsy |
| `NaN` | falsy | 不存在（用 float('nan')，为 truthy！） |

```python
# Python 里判断“空”更自然
if not items:            # 覆盖 []、{}、""、None、0
    ...

# 但要“仅 None 才兜底”时必须显式
value = x if x is not None else default     # ✅
value = x or default                        # ⚠️ x 为 0/"" 时也会回退
```

## 18.4 不可变思维：React 与 Python 的冲突

React 生态强调“不可变更新”：

```ts
const next = [...items, newItem];
const sorted = [...items].sort(cmp);
```

Python 很多方法是**原地修改**：

```python
items.append(new_item)      # 原地
items.sort()               # 原地
items.reverse()            # 原地
items.update(...)          # dict 原地
items.add(...)             # set 原地
```

需要不可变风格：

```python
new_items = [*items, new_item]
sorted_items = sorted(items, key=cmp)
merged = {**a, **b}
new_set = a | b
```

**结论**：写 Python 时要先看某个方法返回什么——`None` 往往意味着“原地修改”。

## 18.5 作用域与闭包的差异

```python
# 块级作用域：Python 没有
for i in range(3):
    pass
print(i)             # 2  ← 泄漏

# 函数内赋值 = 局部变量
x = 1
def f():
    # print(x)       # 若下面有 x = 2，这里会 UnboundLocalError
    x = 2
f()
print(x)             # 1

# 修改外部变量要显式声明
def g():
    global x
    x = 2
g()
print(x)             # 2
```

## 18.6 数字与 ID 的精度问题

```python
big = 10 ** 20 + 1
print(big)                    # 100000000000000000001（精确）

import json
print(json.dumps({"id": big}))   # 仍然是精确数字
# 但 JS 的 JSON.parse 会变成 100000000000000000000 → 精度丢失
```

**实践**：跨前后端传大整数（雪花 ID、订单号）时**用字符串**。本项目的 `exam_id`、`question_id` 都是字符串。

## 18.7 类型系统的差异

| 维度 | TypeScript | Python |
| --- | --- | --- |
| 检查时机 | 编译期（必需） | 运行期注解 + mypy（可选） |
| 类型转换 | 隐式（`"1" + 1`） | 无隐式（抛 TypeError） |
| 结构类型 | 默认结构化 | 名义为主，`Protocol` 提供结构化 |
| 空安全 | `strictNullChecks` | `Optional` + mypy 严格模式 |
| 类型擦除 | 是 | 注解保留在 `__annotations__` |
| 运行时校验 | 需 zod/io-ts | Pydantic / typeguard |

## 18.8 工程习惯差异

| 主题 | 前端习惯 | Python 习惯 |
| --- | --- | --- |
| 命名 | camelCase | snake_case（类 PascalCase） |
| 文件组织 | 一个组件一个文件 | 按功能/领域划分模块与包 |
| 错误处理 | try/catch + 返回值 | 异常 + `with` 资源管理 |
| 日志 | console.log | logging（分级 + 结构化） |
| 配置 | .env + dotenv | os.environ / pydantic-settings |
| 测试 | vitest/jest | pytest（更少样板） |
| 格式化 | prettier（+eslint） | ruff format（+ruff check） |
| 依赖锁 | package-lock/pnpm-lock | uv.lock / requirements.txt |
| 并发 | event loop（默认异步） | 默认同步，需要时显式 asyncio |
| 迭代 | 数组方法链 | 推导式 + 生成器 |

## 18.9 迁移期“条件反射”替换表

| 你习惯写的（TS） | Python 写法 |
| --- | --- |
| `arr.map(f)` | `[f(x) for x in arr]` |
| `arr.filter(f)` | `[x for x in arr if f(x)]` |
| `arr.reduce(f, init)` | `functools.reduce`（更常用 for 累加） |
| `Object.entries(o)` | `o.items()` |
| `o[k] = v` | `d[k] = v`（同） |
| `"k" in o` | `"k" in d`（只查自身键） |
| `typeof x === "string"` | `isinstance(x, str)` |
| `x?.y` | `getattr(x, "y", None)` |
| `arr.length === 0` | `not arr` |
| `arr.includes(x)` | `x in arr` |
| `Array.from(new Set(a))` | `list(set(a))` / `list(dict.fromkeys(a))` |
| `JSON.stringify(o, null, 2)` | `json.dumps(o, ensure_ascii=False, indent=2)` |
| `parseInt(s, 10)` | `int(s)`（非法值抛异常） |
| `throw new Error(m)` | `raise ValueError(m)` |
| `try { } catch (e) { }` | `try: ... except Exception as e: ...` |
| `for (const [i, v] of arr.entries())` | `for i, v in enumerate(arr):` |
| `async/await` | `async/await`（注意阻塞调用会卡事件循环） |
| `Promise.all([...])` | `asyncio.gather(...)` |
| `Math.floor(a/b)` | `a // b` |
| `a ** b` | `a ** b`（同） |
| `a ?? b` | `a if a is not None else b` |

## 18.10 自查清单（迁移完成度）

- [ ] 我不会再写 `arr.map` / `arr.forEach`。
- [ ] 我知道 `sort()` 原地修改且返回 `None`。
- [ ] 我不再用 `x == None` 或用 `is` 比较数值。
- [ ] 我默认写 `encoding="utf-8"`。
- [ ] 我不会用可变对象做默认参数。
- [ ] 我在循环里拼接字符串会用 `join`。
- [ ] 我知道 `"1" + 1` 会报错而不是得 `"11"`。
- [ ] 我知道 `and/or` 返回操作数本身。
- [ ] 我理解 `None` 与 `0`/`""` 都是假值但互不相等。
- [ ] 我会区分“原地修改”与“返回新对象”的方法。

## 18.11 延伸练习（综合）

```python
# 1. 解析日志并生成 Top N 错误码
from collections import Counter
import re
from pathlib import Path

LINE = re.compile(r"status=(?P<status>\d{3})")

def top_status(path: str, n: int = 5) -> list[tuple[str, int]]:
    counter: Counter[str] = Counter()
    with open(path, encoding="utf-8") as f:
        for line in f:
            m = LINE.search(line)
            if m:
                counter[m.group("status")] += 1
    return counter.most_common(n)

# 2. 不可变式更新配置
def update_config(config: dict, **changes) -> dict:
    return {**config, **changes}

# 3. 安全除零 + 大整数转字符串（跨语言安全）
def percent(correct: int, total: int) -> float:
    return round(correct / total * 100, 1) if total else 0.0

def to_json_id(value: int) -> str:
    return str(value)
```

- [ ] 我能一次性列出 10 个 Python 与 JS 的行为差异。
- [ ] 我能判断一段 Python 代码是否含共享可变状态。
- [ ] 我知道异常模型与特殊值模型的取舍。
