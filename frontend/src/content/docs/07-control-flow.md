# 07 条件与循环

> 主题标签：`control` ｜ 对应考试主题：条件与循环

## 7.1 if / elif / else

```python
score = 85

if score >= 90:
    grade = "A"
elif score >= 80:
    grade = "B"
elif score >= 60:
    grade = "C"
else:
    grade = "D"

print(grade)   # B
```

要点：

- 条件后面必须有冒号 `:`，代码块靠缩进。
- `elif` 是 `else if` 的 Python 写法（写 `else if` 会 `SyntaxError`）。
- 条件不需要括号（加了也不算错，但不符合 PEP 8）。
- **没有 `switch`**：3.10+ 用 `match`（见 7.6）。

真值测试代替与布尔比较：

```python
items = []
if not items:              # ✅ Pythonic
    print("空")

if len(items) == 0:        # ⚠️ 冗长
    ...

if flag == True:           # ❌ PEP 8 不推荐
    ...
if flag:                   # ✅
    ...
```

## 7.2 for 循环

```python
for i in range(5):          # 0 1 2 3 4
    print(i)

for ch in "abc":            # 逐字符
    print(ch)

for item in [10, 20]:       # 逐元素
    print(item)

for key in {"a": 1}:        # 只遍历键
    print(key)

for k, v in {"a": 1}.items():
    print(k, v)
```

`range` 的三种形态：

```python
range(5)          # 0,1,2,3,4
range(2, 6)       # 2,3,4,5
range(0, 10, 3)   # 0,3,6,9
range(5, 0, -1)   # 5,4,3,2,1
len(range(5))     # 5      range 支持 len 与索引
```

`range` 是**惰性对象**，不占大内存。

### enumerate / zip（最常用的两个内置函数）

```python
fruits = ["apple", "banana"]
for i, fruit in enumerate(fruits, start=1):
    print(i, fruit)          # 1 apple / 2 banana

names = ["A", "B", "C"]
scores = [90, 80, 70]
for name, score in zip(names, scores):
    print(name, score)

# 长度不等时按最短的截断；要补齐用：
from itertools import zip_longest
for a, b in zip_longest([1, 2], ["x"], fillvalue="-"):
    print(a, b)   # 1 x / 2 -
```

**不要**写 `for i in range(len(items))` 只为了拿元素；需要索引时用 `enumerate`。

### 字典遍历

```python
d = {"a": 1, "b": 2}
for k in d: ...
for k in d.keys(): ...
for v in d.values(): ...
for k, v in d.items(): ...
```

### 遍历多个序列 / 嵌套

```python
for row in matrix:
    for cell in row:
        ...
# 用推导式展平
flat = [cell for row in matrix for cell in row]
```

## 7.3 while 循环

```python
count = 0
while count < 3:
    print(count)
    count += 1

# 无限循环 + break
while True:
    cmd = input("> ")
    if cmd == "quit":
        break
    print(f"执行 {cmd}")
```

别忘了改变条件变量，否则是**死循环**（`Ctrl+C` 中断）。

```python
# do-while 的替代写法
while True:
    do_something()
    if not condition:
        break
```

## 7.4 break / continue / pass

```python
for i in range(10):
    if i == 3:
        continue        # 跳过本次，进入下一次
    if i == 6:
        break           # 立即结束整个循环
    print(i)            # 0 1 2 4 5

for i in range(3):
    pass                # 占位：什么都不做（占位符，不是注释）
```

`pass` 也用于“先写结构，之后补实现”，避免语法错误。

## 7.5 for...else（Python 特色）

`else` 在**循环没有被 break 打断**时执行，常用于“查找”逻辑：

```python
needle = "x"
for item in ["a", "b"]:
    if item == needle:
        print("找到了")
        break
else:
    print("没找到")     # 循环正常走完才会执行

# 等价写法
found = any(item == needle for item in ["a", "b"])
print("找到了" if found else "没找到")
```

## 7.6 match 语句（Python 3.10+）

```python
def handle(command: str) -> str:
    match command.split():
        case ["go", direction]:
            return f"向 {direction} 走"
        case ["look"]:
            return "你看到了一个门"
        case ["pick", *items]:
            return f"拾取 {', '.join(items)}"
        case _:
            return "无法理解"
```

- 默认分支是 `case _:`（不是 `default:`）。
- **没有 fall-through**（不需要 break）。
- 支持结构化模式匹配：序列、映射、类型、类模式、守卫 `case x if x > 0:`。

## 7.7 循环与作用域（与 JS 的重要差异）

```python
for i in range(3):
    pass
print(i)      # 2  ← 循环变量泄漏到外层！
```

Python 的 `for`/`if` **不创建新作用域**（只有函数、类、模块、推导式才创建），因此循环变量在循环外仍可用。

## 7.8 常见陷阱

**① 迭代时修改集合**

```python
nums = [1, 2, 3, 4]
for n in nums:
    if n % 2 == 0:
        nums.remove(n)      # ❌ 会跳过元素

# ✅ 迭代副本
for n in nums[:]:
    if n % 2 == 0:
        nums.remove(n)

# ✅ 或构建新列表
nums = [n for n in nums if n % 2 != 0]
```

**② 在循环里拼接字符串**（改用 `join`，见第 5 章）

**③ while 忘记自增** → 死循环

**④ 浮点比较做循环条件** → 误差累积，改用整数计数或 `math.isclose`

## 7.9 与 JS/TS 对照

| 需求 | TypeScript | Python |
| --- | --- | --- |
| 多分支 | `if/else if/else` | `if/elif/else` |
| switch | `switch/case` | `match/case`（3.10+） |
| for 计数 | `for (let i=0;i<n;i++)` | `for i in range(n):` |
| for...of | `for (const x of arr)` | `for x in arr:` |
| forEach | `arr.forEach((x,i)=>...)` | `for i, x in enumerate(arr):` |
| 对象遍历 | `for (const k in obj)` | `for k, v in d.items():` |
| 循环变量作用域 | `let` 块级 | 函数级（会泄漏） |
| 立即跳出 | `break` | `break` |
| 跳过本次 | `continue` | `continue` |
| 空语句 | `;` / no-op | `pass` |
| do-while | `do...while` | `while True: ... if not c: break` |

## 7.10 小练习

```python
# 1. FizzBuzz
for n in range(1, 16):
    if n % 15 == 0:
        print("FizzBuzz")
    elif n % 3 == 0:
        print("Fizz")
    elif n % 5 == 0:
        print("Buzz")
    else:
        print(n)

# 2. 手写求和与平均值
def average(nums: list[float]) -> float:
    return sum(nums) / len(nums) if nums else 0.0

# 3. 用 match 实现简单计算器
def calc(op: str, a: float, b: float) -> float:
    match op:
        case "+": return a + b
        case "-": return a - b
        case "*": return a * b
        case "/" if b != 0: return a / b
        case _: raise ValueError(f"不支持的运算: {op}")
```

- [ ] 我知道 `for...else` 的 else 何时执行。
- [ ] 我知道循环变量在循环外仍然存在。
- [ ] 我知道 `match` 的默认分支写法。
- [ ] 我能在遍历的同时安全地删除元素。
