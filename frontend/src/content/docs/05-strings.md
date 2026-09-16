# 05 字符串处理

> 主题标签：`strings` ｜ 对应考试主题：字符串处理

## 5.1 创建与多行

```python
s1 = "double"
s2 = 'single'          # 单双引号等价
s3 = """多行
字符串（保留换行）"""
s4 = ("a" "b" "c")     # 相邻字面量自动拼接 -> 'abc'
s5 = "a" * 3           # 'aaa'
```

转义与原始字符串：

```python
print("tab\tnewline\n")     # \t \n 转义
print(r"C:\new\test")       # raw：反斜杠不当转义（路径、正则常用）
print("他说：\"你好\"")       # 转义引号；也可以外层用单引号
```

字节串：

```python
b = b"abc"                  # bytes
b2 = "你好".encode("utf-8")  # str -> bytes
print(b2.decode("utf-8"))   # bytes -> str
```

## 5.2 索引与切片

```python
s = "python"
#    p  y  t  h  o  n
#    0  1  2  3  4  5
#   -6 -5 -4 -3 -2 -1

print(s[0], s[-1])      # p n
print(s[1:4])           # yth     含头不含尾
print(s[:3])            # pyt     省略 start = 从头
print(s[3:])            # hon     省略 stop = 到末尾
print(s[:])             # python  完整副本
print(s[-3:])           # hon
print(s[::2])           # pto     步长 2
print(s[::-1])          # nohtyp  反转
print(s[10:20])         # ''      越界不报错（切片是安全的）
```

**切片不会抛 IndexError**，但索引会：

```python
s[99]        # IndexError: string index out of range
```

字符串不可变：

```python
# s[0] = "P"    # TypeError: 'str' object does not support item assignment
s = "P" + s[1:] # 只能构造新字符串
```

## 5.3 常用方法速查

```python
s = "  Hello World  "

s.strip()            # 'Hello World'      去首尾空白（另有 lstrip/rstrip）
s.lower(), s.upper() # 'hello world', 'HELLO WORLD'
s.title()            # '  Hello World  '
s.capitalize()       # '  hello world  '
s.replace("World", "Python")   # 支持第三个参数限制次数
s.split()            # ['Hello', 'World']    按空白切分
s.split("o")         # ['  Hell', ' W', 'rld  ']
"a,b,,c".split(",")  # ['a', 'b', '', 'c']
"a b  c".split()     # ['a', 'b', 'c']     连续空白视为一个
"-".join(["a", "b"]) # 'a-b'
"42".zfill(5)        # '00042'
"abc".center(7, "*") # '**abc**'
"abc".startswith(("a", "x"))    # True  元组参数
"abc".endswith("c")             # True
"banana".find("na")             # 2     找不到返回 -1
"banana".index("na")            # 2     找不到抛 ValueError
"banana".count("na")            # 2     不重叠计数
"abc123".isalnum()              # True
"123".isdigit()                 # True
"a b".isspace()                 # False
"abc".isalpha()                 # True
"Hello".casefold()              # 'hello'  国际化的大小写比较
"a-b".partition("-")            # ('a', '-', 'b')
"line1\nline2".splitlines()     # ['line1', 'line2']
```

大小写不敏感比较：

```python
print("PyThOn".lower() == "python")   # True
```

## 5.4 格式化：f-string（首选）

```python
name, score = "Alice", 95.5678

print(f"{name} 得分 {score}")            # Alice 得分 95.5678
print(f"{score:.2f}")                    # 95.57      保留两位小数
print(f"{score:10.2f}|")                 # '     95.57|'  宽度 10 右对齐
print(f"{score:<10.2f}|")                # 左对齐
print(f"{score:^10.2f}|")                # 居中
print(f"{42:05d}")                       # 00042
print(f"{255:#x} {255:b} {255:o}")       # 0xff 11111111 377
print(f"{0.256:.1%}")                    # 25.6%
print(f"{1234567:,}")                    # 1,234,567
print(f"{name=}")                        # name='Alice'   调试语法（3.8+）
print(f"{'yes' if score > 60 else 'no'}")
```

对齐/填充小结：`:<左` `:>右` `:^中`，填充字符写在最前，如 `f"{n:*^9}"`。

## 5.5 其他格式化方式（认识即可）

```python
# str.format
"{} 今年 {} 岁".format("Tom", 18)
"{name} 今年 {age} 岁".format(name="Tom", age=18)

# % 格式化（老代码常见）
"%s 今年 %d 岁" % ("Tom", 18)
"%.2f" % 3.14159
```

新代码统一用 f-string；日志库（logging）用 `%` 风格延迟格式化。

## 5.6 字符串拼接的性能

```python
# 差：循环里 += 会不断创建新字符串，O(n²)
out = ""
for word in words:
    out += word

# 好：join 先算总长度再拼接
out = "".join(words)

# 也可用 StringIO 进行大量写入
from io import StringIO
buf = StringIO()
for word in words:
    buf.write(word)
out = buf.getvalue()
```

## 5.7 遍历与查找

```python
for ch in "abc":
    print(ch)

vowels = "aeiou"
count = sum(1 for ch in "hello world" if ch in vowels)

"abc".find("b")      # 1
"abc".rfind("b")     # 1（从右往左找）
```

用 `in` 做子串判断比 `find(...) != -1` 更清晰：

```python
if "error" in log_line:
    ...
```

## 5.8 与 JS/TS 对照

| 需求 | TypeScript | Python |
| --- | --- | --- |
| 长度 | `s.length` | `len(s)` |
| 取字符 | `s[0]`, `s.at(-1)` | `s[0]`, `s[-1]` |
| 切片 | `s.slice(1, 4)` | `s[1:4]` |
| 反转 | `s.split("").reverse().join("")` | `s[::-1]` |
| 包含 | `s.includes("x")` | `"x" in s` |
| 去空白 | `s.trim()` | `s.strip()` |
| 分隔转数组 | `s.split(",")` | `s.split(",")` |
| 数组转字符串 | `arr.join("-")` | `"-".join(arr)` |
| 替换 | `s.replace(/x/g, "y")` | `s.replace("x", "y")` 或 `re.sub` |
| 模板字符串 | `` `${a}` `` | `f"{a}"` |
| 填充 | `s.padStart(5, "0")` | `s.zfill(5)` / `f"{n:05d}"` |
| 不可变 | 是 | 是 |

## 5.9 小练习

```python
# 1. 回文判断
def is_palindrome(text: str) -> bool:
    cleaned = "".join(ch.lower() for ch in text if ch.isalnum())
    return cleaned == cleaned[::-1]

# 2. 单词首字母大写（不用 title）
def capitalize_words(sentence: str) -> str:
    return " ".join(w[:1].upper() + w[1:] for w in sentence.split())

# 3. 输出对齐表格
rows = [("apple", 3), ("banana", 12)]
for name, qty in rows:
    print(f"{name:<8}{qty:>5}")
```

- [ ] 我知道 `"python"[1:4]` 与 `[::-1]` 的结果。
- [ ] 我能解释为什么 `s[0] = "x"` 报错。
- [ ] 我能写出 `f"{3.14159:.2f}"` 的输出。
- [ ] 我知道 `"a,b,,c".split(",")` 的长度是 4。
