# 04 运算符与表达式

> 主题标签：`operators` ｜ 对应考试主题：运算符与表达式

## 4.1 算术运算符

```python
print(2 + 3)      # 5
print(2 - 3)      # -1
print(2 * 3)      # 6
print(2 ** 10)    # 1024    幂运算（JS 用 Math.pow 或 **）
print(7 / 2)      # 3.5
print(7 // 2)     # 3       整除（向下取整）
print(7 % 2)      # 1       取模
print(abs(-3))    # 3
print(pow(2, 10)) # 1024；pow(2, 10, 100) 可做模幂
```

取模在负数上的行为与 JS 不同：

```python
print(-7 % 3)     # 2（Python）    JS: -7 % 3 === -1
print(7 % -3)     # -2（Python）   JS: 1
```

## 4.2 比较运算符

```python
print(1 == 1.0)      # True    值相等
print(1 is 1.0)      # False   身份不同（int 与 float 是两个对象）
print("a" < "b")     # True    字符串按码位比较
print(1 < 2 < 3)     # True    链式比较（Python 特色）
print(1 < 3 > 2)     # True    等价于 1 < 3 and 3 > 2
```

链式比较的中间表达式只求值一次：

```python
def f():
    print("只调用一次")
    return 5

print(0 < f() < 10)
```

- `==` 比较值（调用 `__eq__`），**不做隐式类型转换**：`"1" == 1` 是 `False`。
- `is` 比较身份（`id()` 是否相同）。只对 `None`、`True`、`False` 与单例推荐使用。
- 没有 `===`：因为 `==` 已经足够严格。

```python
a = [1, 2]
b = [1, 2]
print(a == b)   # True   内容相同
print(a is b)   # False  不是同一对象
```

## 4.3 逻辑运算符：and / or / not

**关键特性：返回操作数本身，而不是布尔值。**

```python
print("a" or "b")     # 'a'     第一个真值
print("" or "b")      # 'b'     第一个真值（跳过假值）
print("a" and "b")    # 'b'     最后一个值（前面都为真）
print(0 and "b")      # 0       遇到假值立即返回
print(not "")         # True
print(not [])         # True
```

常用惯用法：

```python
name = user_input or "匿名"        # 空字符串/None 时给默认值（注意 0 也会被替换！）
value = cfg.get("n") if cfg.get("n") is not None else 0   # 更精确的兜底
```

短路求值（与 JS 一致）：

```python
print(0 and 1 / 0)    # 0，右侧不会执行
print(1 or 1 / 0)     # 1
```

## 4.4 条件表达式（三元）

```python
label = "正数" if x > 0 else "非正数"
# 嵌套要谨慎
level = "高" if score > 90 else ("中" if score > 60 else "低")
```

`x > 0 ? a : b` 是 JS 的写法，Python 中不存在。

## 4.5 位运算符

```python
a, b = 0b1010, 0b0110      # 10, 6
print(a & b)      # 2      按位与   0010
print(a | b)      # 14     按位或   1110
print(a ^ b)      # 12     按位异或 1100
print(~a)         # -11    取反：~x == -x - 1
print(a << 2)     # 40     左移（等价 * 4）
print(a >> 1)     # 5      右移（等价 // 2）
```

位运算常见于标志位、权限、哈希与底层协议。

```python
READ, WRITE, EXEC = 1, 2, 4
perm = READ | WRITE
print(bool(perm & WRITE))    # True
perm |= EXEC
perm &= ~WRITE
```

## 4.6 赋值与增强赋值

```python
x = 1
x += 1     # 2
x -= 1
x *= 2
x /= 2     # 结果是 float
x //= 2
x %= 2
x **= 2
```

注意：对列表 `+=` 等价于 `extend`（原地修改），而 `+` 返回新列表：

```python
a = [1]
b = a
a += [2]        # 原地修改，a 与 b 都变 [1, 2]
a = a + [3]     # 新对象，只有 a 变成 [1, 2, 3]
```

海象运算符（3.8+，赋值表达式）：

```python
while (line := input("> ")) != "quit":
    print(line)
```

## 4.7 成员运算符与身份运算

```python
print(2 in [1, 2, 3])         # True
print("na" in "banana")       # True
print("a" not in {"a": 1})    # False  判断键

# 身份
print(None is None)           # True
print([] is [])               # False
```

## 4.8 运算符优先级（从高到低，节选）

| 优先级 | 运算符 |
| --- | --- |
| 1 | `**` |
| 2 | `+x`, `-x`, `~x`（一元） |
| 3 | `*`, `/`, `//`, `%` |
| 4 | `+`, `-` |
| 5 | `<<`, `>>` |
| 6 | `&` |
| 7 | `^` |
| 8 | `|` |
| 9 | `==`, `!=`, `<`, `<=`, `>`, `>=`, `is`, `in` |
| 10 | `not` |
| 11 | `and` |
| 12 | `or` |
| 13 | `if...else`（条件表达式） |
| 14 | `:=`, `lambda` |

```python
print(2 + 3 * 4 ** 2)    # 50  →  4**2=16, 3*16=48, 2+48
print(not 1 == 2)        # True   → not (1 == 2)
print(1 + 2 == 3 and 4 > 2)   # True
```

不确定时**加括号**，可读性优先。

## 4.9 字符串与序列运算

```python
print("py" + "thon")      # python
print("ab" * 3)           # ababab
print([1] + [2])          # [1, 2]
print([0] * 3)            # [0, 0, 0]
print(len("abc"))         # 3
print("a" * 0)            # ''
```

> 陷阱：`[[0] * 2] * 3` 会共享内层列表（见第 6 章）。

## 4.10 与 JS/TS 对照

| 需求 | TypeScript | Python |
| --- | --- | --- |
| 幂 | `2 ** 3` / `Math.pow` | `2 ** 3` |
| 整除 | `Math.trunc(a / b)` | `a // b` |
| 取模符号 | 跟被除数 | 跟除数 |
| 逻辑与 | `a && b`（返回操作数） | `a and b`（返回操作数） |
| 逻辑或 | `a \|\| b` | `a or b` |
| 逻辑非 | `!a` | `not a` |
| 三元 | `a ? b : c` | `b if a else c` |
| 空值合并 | `a ?? b` | `a if a is not None else b` |
| 可选链 | `obj?.x?.y` | `getattr(obj, "x", None)` |
| 严格相等 | `===` | `==`（无隐式转换） |
| 链式比较 | 不支持 | `0 < x < 10` |

## 4.11 小练习

```python
# 1. 用位运算判断奇偶
n = 7
print("奇数" if n & 1 else "偶数")

# 2. 权限检查
def has_perm(perm: int, flag: int) -> bool:
    return bool(perm & flag)

# 3. 安全兜底
def pick(a, b):
    return a if a is not None else b
```

- [ ] 我能说出 `-7 // 2` 与 `-7 % 3` 的值。
- [ ] 我知道 `"a" or "b"` 返回 `"a"` 而不是 `True`。
- [ ] 我能解释 `~5 == -6`。
- [ ] 我知道 `a += [1]` 对列表是原地修改。
