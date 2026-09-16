# 02 基础语法：缩进、变量、输入输出

> 主题标签：`basics` ｜ 对应考试主题：基础语法与变量

## 2.1 缩进是语法

```python
if True:
    print("属于 if 的代码块")
    print("同一缩进 = 同一个块")
print("回到顶层")
```

- 同一代码块缩进必须一致，推荐 **4 个空格**。
- 冒号 `:` 表示“下面开始一个新块”。
- 缩进不一致 → `IndentationError`；`Tab` 与空格混用也会报错。

对照 TypeScript：

```ts
if (true) {
  console.log("缩进只是风格，{} 才是语法");
}
```

## 2.2 变量：名字绑定到对象

```python
x = 1              # 整数
x = "hello"        # 合法：变量只是名字，可以重新绑定到别的类型
name = "Alice"
PI = 3.14159       # 常量靠命名约定（全大写），语言层面没有 const
```

- **无需声明类型**：`int x = 1` 这种写法在 Python 中不存在。
- **赋值 = 绑定引用**，不是复制值：

```python
a = [1, 2]
b = a              # b 与 a 指向同一个列表
b.append(3)
print(a)           # [1, 2, 3]  ← 这就是引用语义
```

- Python 没有 `let/const/var`；也不存在变量提升（`hoisting`）。
- 使用未定义变量 → `NameError`（不是 `undefined`）。

### 命名规则

- 只能包含字母、数字、下划线，**不能以数字开头**：`2user` ❌、`user2` ✅。
- 区分大小写：`Name` 与 `name` 是两个变量。
- 不能使用关键字：`import keyword; print(keyword.kwlist)` 可查看全部。
- 允许：`_private`（约定内部使用）、`__dunder__`（语言保留）、`_`（丢弃值）。

```python
_, _, last = (1, 2, 3)     # 只关心最后一个
a, *rest = [1, 2, 3, 4]    # rest == [2, 3, 4]
```

## 2.3 注释与文档字符串

```python
# 单行注释

"""
多行字符串。放在模块/函数/类开头时会成为 docstring，
可用 help(obj) 或 obj.__doc__ 查看，不是“注释”。
"""

def area(r: float) -> float:
    """返回圆面积。"""
    return 3.14159 * r ** 2
```

没有块注释语法（`/* */` 不存在）；多行说明用连续 `#` 或三引号 docstring。

## 2.4 语句与换行

```python
a = 1; b = 2          # 分号可分隔多条语句，但不推荐
total = (1 +
         2 +
         3)           # 括号内可自由换行（推荐）
total = 1 + \
        2             # 反斜杠也能续行（不推荐）
```

- 换行 = 语句结束，一般不加分号。
- 长表达式优先用括号换行，而非反斜杠。

## 2.5 输出：print 的常用参数

```python
print("a", "b", "c")                 # a b c    ← 默认用空格分隔
print("a", "b", sep="-")             # a-b
print("no newline", end="")          # 结尾不换行
print(f"{name} 今年 {age} 岁")        # f-string（见第 5 章）
print("x =", x, "y =", y)            # 调试常用
```

`print` 还可以接收 `file=` 写到别的流（如 `sys.stderr`）。

## 2.6 输入：input()

```python
name = input("请输入姓名：")          # 返回值永远是 str
age = int(input("请输入年龄："))       # 要数字就显式转换
```

安全性：数字输入要防御性处理。

```python
try:
    age = int(input("年龄："))
except ValueError:
    print("请输入整数")
```

## 2.7 常见异常一览（先认识名字）

| 异常 | 触发场景 |
| --- | --- |
| `SyntaxError` | 语法错误，如漏冒号 |
| `IndentationError` | 缩进错误 |
| `NameError` | 使用未定义的名字 |
| `TypeError` | 类型不支持该操作，如 `"1" + 1` |
| `ValueError` | 类型对但值非法，如 `int("abc")` |
| `IndexError` | 序列下标越界 |
| `KeyError` | 字典键不存在 |
| `AttributeError` | 属性不存在 |
| `ZeroDivisionError` | 除零 |

## 2.8 模块入口惯例

```python
def main() -> None:
    print("这里写主逻辑")

if __name__ == "__main__":      # 直接运行本文件时为 True
    main()
```

- 直接 `python app.py`：`__name__ == "__main__"`。
- 被 `import app`：`__name__ == "app"`，因此主逻辑不会执行。
- 好处：同一份代码既能当脚本运行，也能被测试导入。

## 2.9 与 TS 的写法对照表

| 场景 | TypeScript | Python |
| --- | --- | --- |
| 声明变量 | `let x: number = 1` | `x = 1` |
| 常量 | `const X = 1` | `X = 1`（约定） |
| 打印 | `console.log(x)` | `print(x)` |
| 读取输入 | `prompt()`（浏览器） | `input()` |
| 字符串模板 | `` `hi ${name}` `` | `f"hi {name}"` |
| 类型判断 | `typeof x === "number"` | `isinstance(x, int)` |
| 三元 | `a ? b : c` | `b if a else c` |
| 空值 | `null` / `undefined` | `None` |
| 未定义变量 | `undefined` | `NameError` |
| 代码块 | `{}` | 缩进 |

## 2.10 小练习

```python
# 1. 交换两个变量
a, b = b, a

# 2. 读入两个数并输出和
x = float(input("x: "))
y = float(input("y: "))
print(f"sum = {x + y:.2f}")
```

- [ ] 我能解释为什么 `"1" + 1` 报错，而 `"1" + str(1)` 可以。
- [ ] 我知道 `print("a", "b", sep=",")` 的输出。
- [ ] 我能说出 `if __name__ == "__main__":` 的作用。
