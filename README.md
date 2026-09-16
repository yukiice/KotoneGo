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

## Docker 部署（推荐上服务器）

**单容器 = FastAPI 接口 + 前端静态文件 + SQLite**，不需要 nginx、不需要额外数据库、不需要 Node 运行时。

```bash
docker compose up -d --build     # 构建并启动，访问 http://<服务器IP>:8000
docker compose logs -f           # 看日志
docker compose down              # 停止（数据保留在命名卷里）
```

| 项目 | 实测 |
| --- | --- |
| 镜像大小 | 271 MB（多阶段构建，Node 不进最终镜像） |
| 空闲内存 | **36 MB / 上限 320 MB**（`docker stats` 实测） |
| 启动时间 | 约 2 秒，健康检查自动通过 |
| 端口 | 8000（`KOTONE_PORT=8080 docker compose up -d` 可改） |

- 整站：`http://<host>:8000`；接口文档：`http://<host>:8000/api/docs`
- 数据库：命名卷 `kotone-data` 里的 `/data/kotone.db`；题库打进镜像
- 前端产物由后端托管，已开 gzip（主包 650KB → 220KB）与长缓存；**不要再另外起 nginx 或 `npm run dev`**

### 数据备份 / 恢复

```bash
# 备份（导出成一个 .db 文件）
docker compose exec -T kotone sh -c 'cat /data/kotone.db' > kotone-$(date +%F).db

# 恢复（先停服务再覆盖，避免 WAL 不一致）
docker compose stop
docker compose run --rm -T kotone sh -c 'cat > /data/kotone.db' < kotone-2025-01-01.db
docker compose start

# 导出错题本为 CSV（宿主机装了 sqlite3）
docker compose exec -T kotone sh -c 'cat /data/kotone.db' | sqlite3 -header -csv /dev/stdin \
  "SELECT * FROM wrong_questions;" > 错题本.csv
```

### 改题目 / 改文档后怎么生效

| 改了什么 | 怎么生效 |
| --- | --- |
| 题库 JSON（`backend/data/questions/`） | `docker compose up -d --build`；或挂载目录后 `curl -X POST localhost:8000/api/questions/reload` |
| 前端文档 / 页面（`frontend/`） | `docker compose up -d --build`（静态文件在镜像里） |
| 后端代码（`backend/app/`） | `docker compose up -d --build` |

不想每次重新构建镜像改题目，就在 `docker-compose.yml` 里放开这行，然后在服务器上直接编辑 JSON：

```yaml
    volumes:
      - ./backend/data/questions:/app/backend/data/questions:ro
```

### 内存不够时怎么调

```yaml
# docker-compose.yml
    mem_limit: 256m        # 数据库和题库都不大，256m 足够；再低可试 192m
    cpus: 0.5              # 单核小机器可限到 0.5
```

```dockerfile
# Dockerfile：用「非 uvloop」的精简运行时，可再省约 20MB 镜像
RUN pip install fastapi 'uvicorn>=0.30' pydantic
```

> SQLite 单文件 + 单进程（`--workers 1`）就是本项目的部署形态：没有连接池、没有额外内存开销，1 核 512MB 的机器跑起来毫无压力。

### HTTPS / 域名

项目不内置证书。在宿主机上用 Caddy（最简）或 Nginx 反代到 `127.0.0.1:8000` 即可，同时把 compose 的端口改成 `127.0.0.1:8000:8000` 不对外暴露。Caddy 两行配置：

```
learn.example.com {
    reverse_proxy 127.0.0.1:8000
}
```

单容器内前后端同源，因此不需要配置 CORS。

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

# Docker：构建 + 启动 / 查看状态与内存 / 停止
docker compose up -d --build
docker stats --no-stream kotonego
docker compose down
```

---

## 目录结构

```
backend/                 FastAPI + SQLite
  app/                   config / db / question_bank / schemas / service / routers / main
  data/questions/*.json  题库，一个主题一个文件
  scripts/               题库校验、冒烟测试
frontend/                React + TS + Vite
  src/content/docs/*.md  18 章语法文档
  src/content/index.ts   文档清单（新增章节要在这里注册）
  src/pages/             首页 / 文档 / 考试 / 成绩 / 记录 / 错题本 / 统计
  src/components/        Layout / Markdown / QuestionCard / ui
  src/styles/global.css  全部样式（CSS 变量 + 响应式断点）
Dockerfile               多阶段构建：Node 打包前端 → Python 运行时单容器
.dockerignore            构建上下文瘦身
docker-compose.yml       单服务 + 命名卷 + 内存/日志限制 + 健康检查
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
