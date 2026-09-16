# 03 数据类型与类型转换

> 主题标签：`types` ｜ 对应考试主题：数据类型与转换

## 3.1 内置标量类型

| 类型 | 字面量 | 说明 |
| --- | --- | --- |
| `int` | `1`, `-5`, `0xFF`, `1_000_000` | 任意精度，无溢出 |
| `float` | `1.5`, `1e-3`, `float("inf")` | IEEE 754 双精度 |
| `bool` | `True`, `False` | `bool` 是 `int` 的子类 |
| `complex` | `1+2j` | 复数 |
| `str` | `"abc"`, `'abc'`, `"""..."""` | Unicode 字符串，不可变 |
| `bytes` | `b"abc"`, `b"\x00"` | 字节串（二进制数据） |
| `NoneType` | `None` | 唯一实例，表示“没有值” |

```python
print(type(1))          # <class 'int'>
print(type(1.0))        # <class 'float'>
print(type(True))       # <class 'bool'>
print(isinstance(True, int))   # True  ← bool 继承 int
print(True + True)      # 2     ← 布尔值能参与算术
```

### 任意精度整数

```python
print(2 ** 100)         # 1267650600228229401496703205376
print(10 ** 30 + 1)     # 精确，不丢精度
```

与 JS 的 `Number`（53 位安全整数）不同：**Python int 不溢出**。但把大整数发给 JS 前端时要小心精度（建议转字符串）。

## 3.2 除法三兄弟

```python
print(7 / 2)      # 3.5   真除法，结果总是 float
print(7 // 2)     # 3     向下取整的整除，int // int 得 int
print(7 % 2)      # 1     取模（余数）
print(divmod(7, 2))   # (3, 1)  同时拿商和余数
print(-7 // 2)    # -4    向下取整（不是向零截断！）
print(-7 % 2)     # 1     余数符号跟除数走
```

> 与 JS 对比：JS 没有整除运算符，`Math.floor(-7 / 2)` 才是 `-4`。

## 3.3 浮点精度

```python
print(0.1 + 0.2)                 # 0.30000000000000004
print(0.1 + 0.2 == 0.3)          # False
import math
print(math.isclose(0.1 + 0.2, 0.3))   # True  ← 推荐比较方式
from decimal import Decimal
print(Decimal("0.1") + Decimal("0.2") == Decimal("0.3"))   # True（金融计算）
```

`round()` 使用“银行家舍入”（四舍六入五取偶）：

```python
print(round(2.5))     # 2
print(round(3.5))     # 4
print(round(2.675, 2))# 2.67  ← 浮点表示误差导致，不是 2.68
```

## 3.4 真值测试（falsy 值）

以下值在 `if`/`while` 中被视为假：

```python
False, None, 0, 0.0, 0j, "", [], (), {}, set(), b""
```

其余都是真。**注意差异**：`bool("0") is True`（非空字符串），而 JS 里 `"0"` 也是真；但 JS 的 `{}` 和 `[]` 是真，Python 的 `{}` 和 `[]` 是假。

```python
print(bool("0"))     # True
print(bool(""))      # False
print(bool([]))      # False
print(bool([0]))     # True
```

自定义真值：实现 `__bool__` 或 `__len__`。

## 3.5 None 的正确用法

```python
result = None
if result is None:            # 推荐：is 判断身份
    print("无结果")
if result is not None:
    print("有结果")
```

- `None == 0` 是 `False`，但两者都为“假值”。
- 不要写 `x == None`（PEP 8 推荐 `is None`，且自定义 `__eq__` 时更安全）。
- 函数没有 `return` 时返回 `None`。

## 3.6 类型转换函数

```python
int("42")        # 42
int(3.9)         # 3     向零截断
int("0x1f", 16)  # 31    指定进制
float("1.5")     # 1.5
str(3.14)        # '3.14'
bool("")         # False
list("abc")      # ['a', 'b', 'c']
tuple([1, 2])    # (1, 2)
set([1, 1, 2])   # {1, 2}
dict([("a", 1)]) # {'a': 1}
ord("A")         # 65    字符 → Unicode 码位
chr(65)          # 'A'
bin(5)           # '0b101'
hex(255)         # '0xff'
```

失败时报错而不是返回特殊值：

```python
int("abc")     # ValueError: invalid literal for int() with base 10: 'abc'
int(None)      # TypeError: int() argument must be ... not 'NoneType'
```

> 与 JS 对比：`parseInt("abc")` 得到 `NaN`，Python 直接抛异常。这是“强类型 + 异常优先”的体现，也意味着你**必须**显式处理失败。

## 3.7 可变 vs 不可变

| 不可变（可哈希） | 可变（不可哈希） |
| --- | --- |
| `int`, `float`, `bool`, `str`, `tuple`, `frozenset`, `bytes`, `None` | `list`, `dict`, `set`, `bytearray`, 自定义对象（默认） |

```python
s = "abc"
s2 = s.replace("a", "x")   # 返回新字符串
print(s, s2)               # abc xbc

t = (1, [2, 3])            # 元组本身不可变，但内含列表可变
t[1].append(4)             # 合法
print(t)                   # (1, [2, 3, 4])

d = {[1]: "x"}             # TypeError: unhashable type: 'list'
d = {(1, 2): "x"}          # 元组可作键 ✅
```

**为什么 dict 的键要可哈希？** 哈希值必须在对象生命周期内稳定，可变对象做不到；`hash(obj)` 可验证。

## 3.8 类型判断的正确姿势

```python
x = 1
print(type(x) is int)              # 可以，但不支持子类
print(isinstance(x, int))          # 推荐：支持继承
print(isinstance(x, (int, float))) # 一次判断多个类型

class Animal: ...
class Dog(Animal): ...
d = Dog()
print(isinstance(d, Animal))       # True
print(type(d) is Animal)           # False
```

## 3.9 字符串与字节

```python
s = "你好"
print(len(s))                   # 2     字符数（code point）
print(len(s.encode("utf-8")))   # 6     UTF-8 字节数
b = s.encode("utf-8")           # b'\xe4\xbd\xa0\xe5\xa5\xbd'
print(b.decode("utf-8"))        # 你好
```

- `str`：文本（Unicode）；`bytes`：原始字节。
- 读写网络/二进制文件时是 `bytes`；写 `b"a" + "b"` 会 `TypeError`。

## 3.10 对照速查表

| 需求 | TypeScript | Python |
| --- | --- | --- |
| 转整数 | `parseInt(s, 10)` / `Number(s)` | `int(s)` |
| 转浮点 | `parseFloat(s)` | `float(s)` |
| 转字符串 | `String(x)` / `x.toString()` | `str(x)` |
| 转布尔 | `Boolean(x)` | `bool(x)` |
| 安全数字转换 | `Number.isNaN(x)` 检查 | `try/except ValueError` |
| 类型判断 | `typeof` / `instanceof` | `type()` / `isinstance()` |
| 空值 | `null` / `undefined` | `None` |
| 大整数 | `BigInt` | `int`（默认） |
| 精度比较 | 自行实现 | `math.isclose()` |

## 3.11 小练习

```python
# 安全地把用户输入转成整数
def to_int(text: str, default: int = 0) -> int:
    try:
        return int(text.strip())
    except (ValueError, AttributeError):
        return default

print(to_int(" 42 "))   # 42
print(to_int("abc"))    # 0
```

- [ ] 我能解释 `7 / 2`、`7 // 2`、`-7 // 2` 的结果与类型。
- [ ] 我知道 `bool("0")` 与 `bool("")` 的值。
- [ ] 我能说清 `is None` 与 `== None` 的差别。
- [ ] 我知道为什么 list 不能做 dict 的键。
