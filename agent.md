# agent.md · KotoneGo Python 学习平台开发指南

> 这份文件是给「未来的开发者 / AI 编码助手」看的：先读这里，再动手。
> 目标读者画像：**熟悉 React + TypeScript，几乎没写过 Python 的前端开发者**。
> 因此文档、注释、UI 文案统一用中文，并在讲解处主动做 JS/TS 对照。

---

## 1. 项目是什么

一个「Python 语法学习 + 随机抽题考试」的全栈应用：

| 模块 | 内容 |
| --- | --- |
| 语法文档 | 18 章 Markdown，`frontend/src/content/docs/*.md`，网页端渲染（PC/移动端自适应） |
| 题库 | 238+ 道选择题，`backend/data/questions/*.json`，按主题分文件 |
| 考试 | 每次随机抽 10 题（可配），每题 10 分，满分 100；作答后**实时**给出对错、正确选项、正确理由、错因、知识点、对应文档 |
| 错题本 | 答错的题自动入库，记录错误次数 / 最近一次错误选项与时间 / 笔记 / 已掌握标记 |
| 考试记录 | 每场考试落库，含分数、用时、各主题正确率、逐题解析 |
| 统计 | 累计作答、平均分、最高分、各主题正确率、薄弱主题提示 |
| 数据 | SQLite（`backend/data/kotone.db`），随时可用 SQL / 脚本分析 |

---

## 2. 技术栈与目录结构

```
KotoneGo/
├── agent.md                      # ← 你正在读的文件
├── README.md                     # 人类快速上手（含 Docker 部署）
├── .gitignore / .dockerignore
├── .env.example                  # KOTONE_PORT / KOTONE_BIND / KOTONE_EXAM_SIZE（复制成 .env）
├── Dockerfile                    # 多阶段：Node 打包前端 → Python 运行时单容器
├── docker-compose.yml            # 单服务 + 命名卷 + 内存/日志限制 + 健康检查
├── backend/                      # FastAPI + SQLite（Python 3.11+）
│   ├── requirements.txt
│   ├── static/                   # 前端构建产物（由 Docker 拷入，git 忽略；本地开发不存在）
│   ├── app/
│   │   ├── config.py             # 路径、题量、分值、CORS、STATIC_DIR
│   │   ├── db.py                 # sqlite3 建表 + 连接（表结构定义在这里）
│   │   ├── question_bank.py      # 题库加载 + 严格校验 + 主题中文名
│   │   ├── schemas.py            # Pydantic 请求/响应模型
│   │   ├── service.py            # 业务逻辑：抽题、判分、错题本、统计
│   │   ├── main.py               # FastAPI 入口 + 元信息接口 + 前端静态托管
│   │   └── routers/
│   │       ├── exams.py          # /api/exams/*
│   │       └── stats.py          # /api/wrong-questions、/api/stats
│   ├── data/questions/*.json     # 题库（一个主题一个文件）
│   └── scripts/
│       ├── validate_questions.py # 校验题库格式（改完题库必跑）
│       └── smoke_test.py         # 端到端冒烟测试（无需 pytest）
└── frontend/                     # React 18 + TS + Vite
    ├── vite.config.ts            # /api 代理到 127.0.0.1:8000
    └── src/
        ├── api/client.ts         # fetch 封装（唯一出网地点）
        ├── api/types.ts          # 与 Pydantic 模型一一对应的 TS 类型
        ├── content/index.ts      # 文档清单（DOC_META）+ import.meta.glob 加载 md
        ├── content/docs/*.md     # 18 章语法文档
        ├── components/           # Layout / Markdown / QuestionCard / ui
        ├── hooks/useAsync.ts     # 极简 loading/error/reload hook
        ├── pages/                # Home / Docs / Exam / History / WrongBook / Stats
        └── styles/global.css     # 全部样式（CSS 变量 + 移动端断点）
```

设计取舍（有意为之，别轻易改）：

- **后端用标准库 `sqlite3` 而不是 ORM**：依赖少、SQL 直接可读，方便初学者/Agent 直接改。
- **生产只有一个进程**：`uvicorn --workers 1` 同时提供 API 与前端静态文件（`backend/static`），
  没有 nginx、没有 Postgres、没有容器编排，1 核 512MB 机器实测空闲占用 36MB。
- **前端不引入 UI 框架**：一个 `global.css` 搞定，移动端断点在 960px / 640px。
- **文档放前端仓库、题目放后端**：文档变化不影响 API；题目变化不影响构建产物，改完热加载即可。
- **答案不在试卷下发**：创建考试时只返回题干与选项；作答后由后端返回答案与解析（防止“翻源码看答案”）。

---

## 3. 本地运行

```bash
# 后端（终端 1）
cd backend
python3 -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
# 接口文档：http://127.0.0.1:8000/api/docs
# （Swagger 挂在 /api 下，因为单容器部署时 /docs 被站内语法文档页占用了）

# 前端（终端 2）
cd frontend
npm install
npm run dev            # http://localhost:5173（/api 会自动代理到 8000）
```

常用校验命令：

```bash
cd backend  && python3 scripts/validate_questions.py   # 题库格式（改题库后必跑）
cd backend  && .venv/bin/python scripts/smoke_test.py  # 端到端流程（需后端已启动）
cd frontend && npx tsc -b                              # 类型检查
cd frontend && npm run build                           # 生产构建
```

### Docker / 生产模式（单容器，前端由后端托管）

```bash
cp .env.example .env              # 可选：在里面改 KOTONE_PORT（默认 8010）等
docker compose up -d --build      # 构建 + 启动 → http://localhost:8010
docker compose logs -f kotone     # 日志（service 名是 kotone）
docker compose exec kotone sh     # 进容器（数据库在 /data/kotone.db）
docker compose down               # 停止（数据留在命名卷 kotone-data）
```

端口约定：**容器内部永远是 8000**（Dockerfile CMD 里写死），对外端口由根目录 `.env` 的
`KOTONE_PORT`（默认 8010）决定；`KOTONE_BIND` 控制监听地址（默认 `0.0.0.0`，填 `127.0.0.1` 则只允许本机访问）；
`KOTONE_NAME` 控制容器名（默认 `kotonego`，同机跑多份时必改）。
改这些都不需要重新构建镜像，`docker compose up -d` 即可。

- 镜像内：`frontend/dist` 被拷到 `/app/backend/static`，`main.py` 检测到该目录存在就挂载
  静态资源 + SPA catch-all 路由，因此**同一个进程既能跑 API 又能跑网站**。
- 因此改前端/改后端代码都需要重新构建镜像；只有改题库 JSON 可以挂卷 + `POST /api/questions/reload` 热更新。
- 想本地模拟生产模式，不必装 Docker：

```bash
cd frontend && npm run build
rm -rf ../backend/static && cp -r dist ../backend/static
cd ../backend && .venv/bin/uvicorn app.main:app --port 8000   # 打开 http://127.0.0.1:8000
```

环境变量（后端，全部可选）：

| 变量 | 默认 | 说明 |
| --- | --- | --- |
| `KOTONE_DB_PATH` | `backend/data/kotone.db` | SQLite 路径 |
| `KOTONE_EXAM_SIZE` | `10` | 默认题量 |
| `KOTONE_CORS_ORIGINS` | localhost:5173/4173 | 允许的前端来源 |

---

## 4. 数据模型

```
exams(id TEXT PK, created_at, finished_at, status, size, topics JSON, score, correct_count, duration_seconds)
exam_answers(id PK, exam_id FK, question_id, topic, selected, correct_answer, is_correct, answered_at)
question_stats(question_id PK, topic, attempts, correct_count, last_attempt_at)
wrong_questions(question_id PK, topic, wrong_count, last_selected, first_wrong_at, last_wrong_at, mastered, note)
```

关键语义（改动前请先理解）：

1. **创建考试时就为每道题预插一行 `exam_answers`**（`selected=''` 表示未作答）。
   → 刷新/关闭页面后可以续答，题目顺序也不会乱。
2. **重复作答同一题**：先回滚上一次统计影响，再按新答案计入（`service._rollback_answer_stats`）。
3. **答错** → `wrong_questions` upsert，`wrong_count + 1`，`mastered = 0`。
4. **答对** → 若错题本里有该题，`mastered = 1`（错误历史保留）。这就是“错题答对一次算掌握”的规则。
5. **分数** = `round(correct / size * 100)`，满分固定 100（与 `POINTS_PER_QUESTION` 一致）。

---

## 5. API 参考

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/health` | 健康检查 + 题库数量（Docker healthcheck 用它） |
| GET | `/api/meta` | 题库总量、默认题量、主题列表（含每个主题题数） |
| POST | `/api/questions/reload` | 重新加载题库 JSON（改完题目免重启） |
| POST | `/api/exams` | 创建考试 `{size, topics[], difficulty, only_wrong}` → 题目**不含答案** |
| GET | `/api/exams/{id}` | 考试详情：成绩 + 每题作答 + 答案 + 解析 |
| POST | `/api/exams/{id}/answers` | 提交单题 `{question_id, selected}` → 对错 + 理由 + 知识点 |
| POST | `/api/exams/{id}/finish` | 交卷，写入 `duration_seconds` |
| GET | `/api/exams?limit&offset` | 考试历史 |
| DELETE | `/api/exams/{id}` | 删除一场考试 |
| GET | `/api/wrong-questions?topic&mastered` | 错题列表（含完整题目与解析） |
| PATCH | `/api/wrong-questions/{qid}` | `{mastered, note}` |
| DELETE | `/api/wrong-questions/{qid}` | 移出错题本 |
| GET | `/api/stats` | 总体统计 + 各主题正确率 + 最近考试 |

---

## 6. 最常见的任务：**补充题目**

### 6.1 题目 JSON 结构

文件位置：`backend/data/questions/NN-<topic>.json`

```json
{
  "topic": "types",
  "label": "数据类型与转换",
  "questions": [
    {
      "id": "types-17",
      "topic": "types",
      "difficulty": "easy",
      "question": "题干，可以包含 \\n 换行展示代码",
      "options": { "A": "选项一", "B": "选项二", "C": "选项三", "D": "选项四" },
      "answer": "B",
      "explanation": "正确答案为什么是 B（这是答对时展示的“理由”）",
      "distractors": {
        "A": "选 A 为什么错",
        "C": "选 C 为什么错",
        "D": "选 D 为什么错"
      },
      "knowledge": ["知识点1", "知识点2"],
      "doc": "03-data-types",
      "tags": ["pitfall"]
    }
  ]
}
```

字段规则（`question_bank._validate` 会强制检查）：

| 字段 | 必填 | 说明 |
| --- | --- | --- |
| `id` | ✅ | 全局唯一，命名 `<topic>-<序号>`；**不要复用已删除的 id**（历史记录会指向它） |
| `topic` | ✅ | 必须是已在 `TOPIC_LABELS` 注册的主题键 |
| `question` | ✅ | 题干纯文本，代码用 `\n` 换行 |
| `options` | ✅ | 至少 2 个；键用 `A/B/C/D`（前端按此顺序渲染，支持到 F） |
| `answer` | ✅ | 必须是 `options` 里存在的键 |
| `explanation` | ✅ | 答对时的理由，**必写**，否则反馈面板会空 |
| `difficulty` | 建议 | `easy` / `medium` / `hard`，默认 `easy`；用于难度筛选 |
| `distractors` | 强烈建议 | 每个错误选项的错因；缺了前端会显示“暂无专门错因”的兜底文案 |
| `knowledge` | 建议 | 知识点标签，展示在反馈面板 |
| `doc` | 建议 | 对应文档 slug（`frontend/src/content/docs/` 的文件名，不含 `.md`），错题可直接跳文档 |
| `tags` | 可选 | 自定义标签，如 `pitfall`、`js-compare` |

### 6.2 写题规范（保证“能学到东西”）

1. **每道题必须有明确的唯一正确答案**，避免“也说得通”的歧义选项。
2. **错因要具体**：不要写“这是错的”，要写“这是 JS 的行为 / 这是 Python 2 的写法 / 顺序反了”。
3. **优先考易错点**：可变默认参数、`sort()` 返回 `None`、`//` 负数、`is` vs `==`、`bool("0")`、生成器一次性……
4. **和 JS/TS 对比的题很适合本项目**：题干里可以直接写「TS 里写作 X，Python 中对应什么」。
5. **难度分布**：`easy` 约 50%、`medium` 约 35%、`hard` 约 15%，让随机 10 题有梯度。
6. **解释里给可验证的结论**：例如「`-7 // 2 == -4`，因为 `//` 是向下取整」，而不是模糊描述。
7. 代码里**不要**用需要外部依赖的例子（只考标准库/语言本身）。

### 6.3 加题流程（照抄即可）

```bash
# 1. 在对应主题文件末尾追加题目（注意 JSON 逗号）
$EDITOR backend/data/questions/03-types.json

# 2. 校验（会检查必填字段、answer 是否在 options、id 是否重复）
cd backend && python3 scripts/validate_questions.py

# 3. 让运行中的后端重新加载（免重启）
curl -X POST localhost:8000/api/questions/reload

# 4. 冒烟测试（可选，但改了 service 一定要跑）
.venv/bin/python scripts/smoke_test.py
```

### 6.4 新增一个**主题**

四步，缺一不可：

1. `backend/app/question_bank.py` 的 `TOPIC_LABELS` 里加中文名：
   `"regex": "正则表达式",`
2. 新建 `backend/data/questions/18-regex.json`（`topic` 字段填新键）。
3. `frontend/src/content/index.ts` 的 `DOC_META` 里加一章（`topic` 字段填新键），并在 `content/docs/` 放同名 `.md`。
4. 跑 `validate_questions.py` + `npx tsc -b`，确认前后端都认这个主题。

---

## 7. 扩展文档（Markdown 章节）

- 位置：`frontend/src/content/docs/<slug>.md`，slug 采用 `NN-kebab-case`（例：`14-files-json.md`）。
- 在 `frontend/src/content/index.ts` 的 `DOC_META` 里注册（`title` / `summary` / `topic`）。
- 侧边栏、上一章/下一章、本页目录、搜索都由 `DOC_META` 驱动，无需改组件。
- Markdown 支持 GFM（表格、任务清单）+ 代码高亮；`##`/`###` 标题会生成锚点（TOC 用）。
- 建议每章结构固定：**概念 → 代码示例 → 与 JS/TS 对照表 → 常见坑 → 自测清单**，与已有 18 章保持一致风格。

```bash
# 新增章节后确认构建通过（文档是打包进 bundle 的）
cd frontend && npm run build
```

---

## 8. 扩展后端功能

顺序永远是 **schema → service → router → 前端 types → client → 页面**：

1. `app/schemas.py`：加 Pydantic 模型（请求体 + 响应体）。
2. `app/service.py`：写业务逻辑与 SQL；抛 `NotFoundError`（→404）/ `ConflictError`（→400）。
3. `app/routers/*.py`：只做 HTTP 映射（`_handle` 统一把异常转成 HTTPException）。
4. 需要新表/新列 → 改 `app/db.py` 的 `SCHEMA`（`CREATE TABLE IF NOT EXISTS`，重启即生效；
   若要改已有表的列，需要写迁移或直接删库重建）。
5. `frontend/src/api/types.ts` 加类型 → `api/client.ts` 加方法 → 页面使用。

参考实现范例：错题本（`service.list_wrong_questions` → `routers/stats.py` → `WrongBookPage.tsx`）。

---

## 9. 扩展前端

- 路由集中在 `src/App.tsx`；新页面放 `src/pages/`，用 `Layout` 的 `<Outlet/>` 包裹即可获得导航与页脚。
- 数据获取统一用 `useAsync(() => api.xxx(), [deps])`（返回 `{data, loading, error, reload}`）。
  数据量大或需要缓存时，可平滑替换成 TanStack Query，`api/client.ts` 不用改。
- 样式：只改 `src/styles/global.css`，用 `--brand/--ok/--bad` 等 CSS 变量，避免引入 UI 框架。
- 响应式断点：`960px`（文档侧栏收起 → 顶部下拉）、`640px`（栅格变单列、字号下调）。
- 无障碍/移动端注意：选项按钮用 `<button>`、保留 `env(safe-area-inset-*)`、避免横向滚动（表格已包 `.table-wrap`）。

---

## 10. 已知约束与坑（改动时留意）

1. **题目 id 一旦发布不要改**：`exam_answers.question_id`、`wrong_questions.question_id` 都引用它；
   改 id 会导致历史记录/错题本失联（`service` 会跳过找不到的题，表现为“题目变少”）。
2. **`doc` slug 必须与 `DOC_META` 完全一致**，否则错题里的文档链接 404。
3. **`TOPIC_LABELS` 缺主题**时，前端只显示英文 topic 键，不影响运行但体验差。
4. **不要在下发试卷的响应里带上 `answer`**（`Question.public()` 与 `revealed()` 已分开）。
5. **不要用 `list()` 装饰器缓存题库后又期待热更新**：`load_questions` 有 `lru_cache`，
   改题后调用 `reload_questions()`（或 `POST /api/questions/reload`）。
6. `TopicStat.accuracy` 与 `Stats.avg_score` 都是“四舍五入到 1 位/整数”，前端不要再叠加取整。
7. **前端 `import.meta.glob` 是 eager 的**：18 章文档会进主 bundle（约 220KB gzip）。
   若文档数量大增，改成懒加载：`import.meta.glob('./docs/*.md', { query: '?long' ... })` 并用 `React.lazy`
   或 `useEffect` 动态 `import()`。
8. **Python 版本要求 3.11+**（用了 `X | None`、`match`、`tomllib` 等）；容器里固定为 `python:3.12-slim`。
9. **Swagger 文档在 `/api/docs` 而不是 `/docs`**：`/docs` 已经被站内的「语法文档」页面占用
   （单容器部署时前端路由和后端路由同一个域名）。新增路由时别再用 `/docs`、`/redoc`。
10. **静态托管是条件性的**：`backend/static` 不存在时不注册 catch-all 路由（本地开发/测试行为不变）。
   不要在 `backend/app/` 里引用 `frontend/src` 的任何东西。
11. **容器内以 non-root（uid 10001）运行**：把宿主目录 bind mount 到 `/data` 时要
    `sudo chown -R 10001:10001 <目录>`，否则写库报 `unable to open database file`；
   用命名卷（默认）没有这个问题。
12. **不要给容器加 `--reload` 或 `--workers >1`**：SQLite 单写者 + 小内存，多 worker 只会增加内存且有写锁竞争。
13. **`container_name` 是可覆盖的（`KOTONE_NAME`）**：compose 里写死容器名时，
    同一台机器上第二份 checkout 执行 `up` 会报 `Conflict. The container name "/kotonego" is already in use`。
    同机多实例就加 `KOTONE_NAME` + `KOTONE_PORT`，两套独立命名卷互不影响。

---

## 11. 下一步可以做什么（Roadmap 建议）

按“性价比”排序：

1. **间隔重复（SRS）**：给 `wrong_questions` 加 `due_at` / `ease`，错题按 SM-2 排期复现 → 复习效率最高。
2. **按选项生成题目变体**：同一知识点换问法，减少“记住了答案位置”的假成绩。
3. **导出/导入**：`GET /api/wrong-questions/export` 输出 Markdown/Anki CSV，方便离线背。
4. **考试模式增强**：限时模式、错题加权抽题（`question_stats` 已有正确率数据）、只考“从未见过”的题。
5. **题目质量反馈**：对每道题支持「这题有问题」上报（新表 `question_reports`）。
6. **前端代码分割**：把 `react-markdown` + `highlight.js` 拆成 lazy chunk，首屏更快。
7. **部署增强**：GitHub Actions 自动构建镜像（含 `linux/arm64`，便宜 ARM 小鸡可用）、
   每日 `sqlite3 .backup` 定时任务、`/api/health` 接入 uptime 监控。
8. **测试**：把 `scripts/smoke_test.py` 升级成 pytest，覆盖抽题边界（题量不足、错题池为空）。

---

## 12. 编码约定

- 后端：`snake_case`、类型注解齐全、`from __future__ import annotations`、函数写 docstring（中文即可）。
- 前端：函数组件 + hooks，不用 class 组件；类型放 `api/types.ts`，不要在页面里随手 `any`。
- 提交信息：`feat(quiz): 新增正则主题 30 题`、`fix(api): 修正重复作答的统计回滚`。
- 分支：功能分支 `python/0.0.1`（当前），大改动请开新分支。
- 改完必做：`validate_questions.py` → `npx tsc -b` → `npm run build` → `smoke_test.py`。
