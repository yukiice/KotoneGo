# 01 起点：Python 与前端世界的差异

> 本章目标：把 Python 的运行方式、工具链、项目结构和你已经熟悉的 Node/npm 世界对应起来。

## 1.1 Python 是什么

- **解释型 + 动态强类型** 语言：不需要编译步骤，变量类型在运行时确定，但不会做隐式类型转换。
- **缩进即语法**：没有 `{}`，代码块由缩进（推荐 4 个空格）决定。
- **一切皆对象**：函数、类、模块、整数都是对象，函数可以像变量一样传递（和 JS 一致）。
- **标准库非常强大**：`json`、`csv`、`sqlite3`、`pathlib`、`datetime`、`asyncio`、`http.server` 开箱即用。

与 JS/TS 的总体对照：

| 维度 | Python | JS/TS |
| --- | --- | --- |
| 运行方式 | `python app.py` | `node app.js` |
| 包管理 | `pip` + `requirements.txt` / `pyproject.toml` | `npm` + `package.json` |
| 虚拟环境 | `venv`（隔离依赖） | 每个项目的 `node_modules` |
| 类型系统 | 动态强类型 + 可选注解（mypy） | 动态弱类型 + TS 静态类型（tsc） |
| 类型检查器 | mypy / pyright | tsc |
| 代码块 | 缩进 | `{}` |
| 空值 | `None` | `null` / `undefined` |
| 异常 | `try/except/finally` | `try/catch/finally` |
| 模块 | `import x` / `from x import y` | `import x` / `require` |
| 异步 | `async/await` + asyncio 事件循环 | `async/await` + Promise |
| 测试 | pytest / unittest | jest / vitest |
| 格式化 | black / ruff format | prettier |
| 静态检查 | ruff / flake8 / mypy | eslint / tsc |

## 1.2 安装与版本

```bash
python3 --version      # 例如 Python 3.14.7
python3 -m pip --version
```

macOS 用 Homebrew：`brew install python@3.12`；Windows 用官网安装包（勾选 “Add python.exe to PATH”）。

## 1.3 三种运行方式

```bash
python3                     # 1. 进入交互式 REPL（适合试验语法，类似 node 直接回车）
python3 hello.py            # 2. 执行脚本
python3 -c "print(1 + 1)"   # 3. 执行一行代码
```

`hello.py`：

```python
# 第一个脚本
print("Hello, Python!")   # 输出并换行
```

REPL 里的 `_` 保存上一次的结果，`exit()` 或 `Ctrl+D` 退出。

## 1.4 虚拟环境：Python 版的 node_modules

每个项目一个独立环境，避免污染全局：

```bash
cd my-project
python3 -m venv .venv              # 创建
source .venv/bin/activate          # macOS/Linux 激活；Windows: .venv\Scripts\activate
pip install -r requirements.txt    # 安装依赖
python app.py                      # 此后 python 就是 .venv 里的
deactivate                         # 退出
```

把依赖写进 `requirements.txt`：

```bash
pip install fastapi uvicorn
pip freeze > requirements.txt      # 导出当前环境所有依赖及版本
```

> 注解：`pip freeze` 导出的是“完整环境快照”。现代项目更推荐 `pyproject.toml` + `uv`/`poetry` 管理依赖分组。

## 1.5 项目结构约定

```
my-project/
├── .venv/                  # 虚拟环境（不要提交）
├── app/
│   ├── __init__.py         # 让目录成为“包”
│   ├── main.py             # 入口
│   └── utils.py
├── tests/
│   └── test_main.py
├── data/
├── requirements.txt
└── README.md
```

`.gitignore` 需要包含：

```
.venv/
__pycache__/
*.pyc
.env
```

## 1.6 代码风格：先记住这几条

- 缩进 4 个空格，不要混用 Tab。
- 变量/函数 `snake_case`，类名 `PascalCase`，常量 `UPPER_SNAKE`。
- 每行不超过 79~100 字符（团队协商，ruff/black 可自动格式化）。
- 用 f-string 格式化字符串，不用 `%` 或 `+` 拼接。
- 官方风格指南：PEP 8；命名/注释规范：PEP 257（docstring）。

```python
def calc_total_price(unit_price: float, quantity: int) -> float:
    """计算总价：单价 * 数量。"""
    return unit_price * quantity
```

## 1.7 推荐的开发工具链（对应前端习惯）

| 前端 | Python |
| --- | --- |
| ESLint + Prettier | `ruff check` + `ruff format`（极快，一个工具搞定） |
| tsc | `mypy .` / `pyright` |
| Jest/Vitest | `pytest -q` |
| nodemon | `uvicorn app:app --reload` / `watchfiles` |
| nvm | `pyenv` / `uv python install` |

安装与使用：

```bash
pip install ruff mypy pytest
ruff check . && ruff format .
mypy .
pytest -q
```

## 1.8 常见误区速览

1. **不要用 `is` 比较数字或字符串的值**（`a is 1` 是身份比较，只有 `None/True/False` 和单例推荐用 `is`）。
2. **缩进错误就是语法错误**，粘贴代码时最容易出问题。
3. **`input()` 返回字符串**，要数字必须 `int(...)`。
4. **字符串不可变**，`s[0] = "x"` 会报错。
5. **可变默认参数**是经典陷阱，见第 8 章。
6. **`/` 永远返回 float**，整数除用 `//`。

## 1.9 自测清单

- [ ] 我能创建并激活虚拟环境，知道 `deactivate` 的作用。
- [ ] 我知道 `python3 file.py` 与 REPL 的区别。
- [ ] 我能说出 3 个 Python 与 JS 的类型系统差异。
- [ ] 我知道 `requirements.txt` 不是自动读取的。

配套练习：考试主题 **基础语法与变量（basics）**。
