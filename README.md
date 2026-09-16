# KotoneGo · Python 学习平台

给 **React / TypeScript 开发者**准备的 Python 语法学习 + 考试系统。
语法讲解全程与 JS/TS 对照，考试答错立即给出正确选项、错因与知识点，错题自动入库，所有数据落到本地 SQLite，方便长期跟踪。

```
语法文档 18 章  ·  题库 238 题 / 17 主题  ·  随机抽题考试  ·  错题本  ·  学习统计
前端 React + TS + Vite（PC / 手机自适应）  ·  后端 FastAPI + SQLite
```

---

## 快速开始

需要 Python 3.11+ 和 Node 18+。

### 1. 启动后端

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

- 接口文档（Swagger）：<http://127.0.0.1:8000/docs>
- 数据库文件：`backend/data/kotone.db`（首次启动自动创建）
- 题库：`backend/data/questions/*.json`

### 2. 启动前端

```bash
cd frontend
npm install
npm run dev
```

打开 <http://localhost:5173> 即可。开发服务器会把 `/api` 代理到 `127.0.0.1:8000`，所以需要先启动后端。

### 3. 生产构建

```bash
cd frontend && npm run build      # 产物在 frontend/dist
```

---

## 功能一览

| 页面 | 路径 | 说明 |
| --- | --- | --- |
| 首页 | `/` | 概览 + 快捷开始考试（题量 / 难度 / 主题可选，也可「只练错题」） |
| 语法文档 | `/docs` | 18 章 Markdown 教程，侧栏目录 + 搜索 + 本页 TOC + 手机端下拉切换 |
| 考试 | `/exam`、`/exam/:id` | 随机抽题，逐题作答，实时反馈，题目导航，进度服务端保存（可续答） |
| 成绩解析 | `/result/:id` | 分数环、各主题正确率、逐题解析、同范围再来一场 |
| 考试记录 | `/history` | 所有场次分数 / 用时 / 状态，可继续或删除 |
| 错题本 | `/wrong` | 错误次数、最后一次错误选项、错因、相关知识点、笔记、已掌握标记、按主题筛选 |
| 统计 | `/stats` | 累计作答、平均分、最高分、各主题正确率、薄弱主题提示 |

### 考试规则

- 默认 10 题，每题 10 分，满分 100（题量可调 5/10/20/30/50）。
- 每题作答后**立刻**显示：正确选项、为什么它正确、你选的选项为什么错、相关知识点、对应文档章节。
- 答错自动进错题本；错题在后续考试中答对一次即标记「已掌握」（错误历史保留）。
- 一场考试可以多次作答同一题（会覆盖上一次结果，统计同步回滚）。
- 桌面端支持键盘：数字键选项、`Enter` / `→` 下一题。

---

## 常用命令

```bash
# 校验题库格式（改完题目必跑）
cd backend && python3 scripts/validate_questions.py

# 端到端冒烟测试（需要后端已启动）
cd backend && .venv/bin/python scripts/smoke_test.py

# 改完题目后让运行中的后端热加载题库
curl -X POST http://127.0.0.1:8000/api/questions/reload

# 前端类型检查 / 构建
cd frontend && npx tsc -b && npm run build
```

---

## 目录结构

```
backend/                 FastAPI + SQLite
  app/                   config / db / question_bank / schemas / service / routers
  data/questions/*.json  题库，一个主题一个文件
  scripts/               题库校验、冒烟测试
frontend/                React + TS + Vite
  src/content/docs/*.md  18 章语法文档
  src/content/index.ts   文档清单（新增章节要在这里注册）
  src/pages/             首页 / 文档 / 考试 / 成绩 / 记录 / 错题本 / 统计
  src/components/        Layout / Markdown / QuestionCard / ui
  src/styles/global.css  全部样式（CSS 变量 + 响应式断点）
agent.md                 开发指南：怎么加题、加章节、扩展接口（**动手前先读**）
```

---

## 我想自己加题 / 加章节 / 加功能

请先读 [agent.md](./agent.md)，里面有：

- 题目 JSON 字段规范与写作规范（含必填字段、错因怎么写、难度分布建议）
- 新增主题的四步流程
- 新增文档章节的规范
- 后端「schema → service → router → 前端 types → client → 页面」扩展顺序
- 已知约束（题目 id 不可改、`doc` slug 必须匹配等）与后续 Roadmap

---

## License

见 [LICENSE](./LICENSE)。
