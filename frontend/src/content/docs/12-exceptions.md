# 12 异常处理

> 主题标签：`exceptions` ｜ 对应考试主题：异常处理

## 12.1 基本结构

```python
try:
    n = int(input("数字："))
    print(10 / n)
except ValueError:
    print("不是合法数字")
except ZeroDivisionError as e:
    print(f"不能除以零：{e}")
else:
    print("一切正常")          # try 没有异常时执行
finally:
    print("无论如何都会执行")   # 清理资源
```

执行顺序：

| 情况 | 执行的分支 |
| --- | --- |
| try 成功 | try → else → finally |
| try 抛 ValueError | except ValueError → finally |
| try 抛未捕获异常 | finally 后继续向上抛 |
| try 里有 return | finally 先执行，再返回 |

## 12.2 异常层次（节选）

```
BaseException
├── SystemExit              # sys.exit()
├── KeyboardInterrupt       # Ctrl+C
├── GeneratorExit
└── Exception               # ← 业务异常都该继承这里
    ├── StopIteration
    ├── ArithmeticError
    │   └── ZeroDivisionError
    ├── LookupError
    │   ├── IndexError      # 序列越界
    │   └── KeyError        # 字典键缺失
    ├── ValueError          # 值非法（int("abc")）
    ├── TypeError           # 类型不支持（"1" + 1）
    ├── AttributeError      # 属性不存在
    ├── FileNotFoundError
    ├── PermissionError
    ├── OSError（IOError 的别名族）
    ├── RuntimeError
    │   └── RecursionError
    └── UnicodeDecodeError
```

**结论**：`except Exception` 能捕获业务异常，但不会捕获 `KeyboardInterrupt`/`SystemExit` —— 这通常是好事。

## 12.3 反模式：裸 except

```python
# ❌ 吞掉所有错误，bug 永远查不出来
try:
    do_something()
except:
    pass

# ❌ 同上，还更隐蔽
try:
    do_something()
except Exception:
    pass

# ✅ 捕获具体异常并处理/记录
try:
    data = json.loads(text)
except json.JSONDecodeError as exc:
    logger.warning("配置解析失败，使用默认值: %s", exc)
    data = {}

# ✅ 至少重新抛出或记录
try:
    risky()
except Exception as exc:
    logger.exception("未预期的错误")
    raise
```

## 12.4 捕获多种异常

```python
try:
    value = int(text)
except (ValueError, TypeError) as exc:    # 元组 + 括号
    print(f"输入无效：{exc}")

# Python 2 写法（在 Python 3 是语法错误）
# except ValueError, TypeError:
```

## 12.5 抛出异常

```python
def set_age(age: int) -> None:
    if not isinstance(age, int):
        raise TypeError(f"age 必须是 int，收到 {type(age).__name__}")
    if age < 0:
        raise ValueError("age 不能为负")

# 在 except 中重抛当前异常
try:
    ...
except ValueError:
    logger.warning("忽略无效值")
    raise            # 裸 raise 保留原始 traceback
```

**不要用异常做正常流程控制**（可预见的失败优先用返回值/默认值）：

```python
# ✅ 可预见：用 get
value = mapping.get(key, default)

# ✅ 可预见：用 in
if key in mapping:
    ...

# ✅ 罕见/异常路径：EAFP
try:
    value = mapping[key]
except KeyError:
    value = default
```

Python 文化的 EAFP（Easier to Ask Forgiveness than Permission）鼓励“先做，出错再处理”，但**不应滥用**在对性能敏感或高频的路径上。

## 12.6 异常链

```python
class ConfigError(Exception):
    """配置错误。"""

try:
    port = int(config["port"])
except (KeyError, ValueError) as exc:
    raise ConfigError(f"配置项 port 无效: {config.get('port')!r}") from exc
```

- `from exc` 设置 `__cause__`，traceback 会显示 “The above exception was the direct cause of...”。
- 不加 `from` 时 Python 仍会记录 `__context__`（隐式上下文）。
- `raise ... from None` 可以显式抑制上下文（少用）。

## 12.7 自定义异常

```python
class AppError(Exception):
    """应用异常基类。"""

class NotFoundError(AppError):
    def __init__(self, resource: str, key):
        super().__init__(f"{resource} 不存在: {key!r}")
        self.resource = resource
        self.key = key

class ValidationError(AppError):
    def __init__(self, field: str, message: str):
        super().__init__(f"{field}: {message}")
        self.field = field

try:
    raise NotFoundError("用户", 42)
except AppError as exc:            # 捕获整个家族
    print(exc)                     # 用户 不存在: 42
```

约定：自定义异常继承 `Exception`（不要继承 `BaseException`），命名以 `Error` 结尾。

## 12.8 常用异常语义速查

| 异常 | 触发 |
| --- | --- |
| `TypeError` | 类型不对：`len(1)`、`"1" + 1` |
| `ValueError` | 类型对但值不对：`int("abc")` |
| `KeyError` | 字典键缺失 |
| `IndexError` | 序列索引越界 |
| `AttributeError` | 属性不存在：`None.foo` |
| `FileNotFoundError` | 打开不存在的文件（OSError 子类） |
| `PermissionError` | 权限不足 |
| `ZeroDivisionError` | 除零（整数与浮点都会抛） |
| `UnicodeDecodeError` | 用错编码读取文本 |
| `json.JSONDecodeError` | JSON 解析失败（ValueError 子类） |
| `RecursionError` | 递归过深 |
| `AssertionError` | `assert` 失败（不要用于校验用户输入） |

## 12.9 with 语句：比 finally 更好的资源管理

```python
# 手动管理（容易遗忘）
f = open("a.txt", encoding="utf-8")
try:
    data = f.read()
finally:
    f.close()

# ✅ 推荐
with open("a.txt", encoding="utf-8") as f:
    data = f.read()
```

多个资源：

```python
with open("in.txt", encoding="utf-8") as src, \
     open("out.txt", "w", encoding="utf-8") as dst:
    dst.write(src.read())
```

自定义上下文管理器：

```python
from contextlib import contextmanager

@contextmanager
def timer(label: str):
    import time
    start = time.perf_counter()
    try:
        yield
    finally:
        print(f"{label} 耗时 {time.perf_counter() - start:.3f}s")

with timer("计算"):
    sum(range(10 ** 6))
```

## 12.10 assert 与异常的取舍

```python
# assert 用于“开发期内部不变式”，可能被 -O 关闭
assert isinstance(items, list), "items 必须是列表"

# 校验用户输入 / 公共 API 参数 → 用异常
if not isinstance(items, list):
    raise TypeError("items 必须是列表")
```

## 12.11 与 JS/TS 对照

| 需求 | TypeScript | Python |
| --- | --- | --- |
| 捕获 | `try/catch/finally` | `try/except/finally` |
| 多类型 | `instanceof` 分支 | `except (A, B):` |
| 抛出 | `throw new Error()` | `raise ValueError()` |
| 错误对象 | `Error` + `cause` | `Exception` + `__cause__` / `from` |
| 自定义错误 | `class E extends Error` | `class E(Exception)` |
| 无条件执行 | `finally` | `finally` |
| 仅成功分支 | 无（写在 try 内） | `else` 子句 |
| 资源释放 | `using` / try-finally | `with` |
| 错误优先 | 返回值可能为 null | 抛异常（不返回特殊值） |

## 12.12 小练习

```python
# 1. 稳定的 JSON 读取
import json
from pathlib import Path

def read_json(path: str, default=None):
    p = Path(path)
    if not p.exists():
        return default
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path} 不是合法 JSON") from exc

# 2. 重试装饰器（见第 16 章）
# 3. 把异常映射成 HTTP 状态码
def to_status(exc: Exception) -> int:
    match exc:
        case NotFoundError(): return 404
        case ValidationError(): return 422
        case PermissionError(): return 403
        case _: return 500
```

- [ ] 我知道 `ValueError` 与 `TypeError` 的区别。
- [ ] 我知道裸 `except:` 为什么危险。
- [ ] 我知道 `else` 与 `finally` 的执行时机。
- [ ] 我知道 `raise X from exc` 的作用。
- [ ] 我知道 `assert` 不适合校验用户输入。
