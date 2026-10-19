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

- 接口文档（Swagger）：<http://127.0.0.1:8000/api/docs>（注意不是 `/docs`，`/docs` 留给站内的语法文档页）
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
cp .env.example .env            # 端口等配置写在这里（可跳过，用默认值）
docker compose up -d --build    # 构建并启动
docker compose logs -f          # 看日志
docker compose down             # 停止（数据保留在命名卷里）
```

| 项目 | 实测 |
| --- | --- |
| 镜像大小 | 271 MB（多阶段构建，Node 不进最终镜像） |
| 空闲内存 | **36 MB / 上限 320 MB**（`docker stats` 实测） |
| 启动时间 | 约 2 秒，健康检查自动通过 |
| 宿主机端口 | **默认 8010**（避开常用的 8000，可改，见下） |

- 整站：`http://<host>:8010`；接口文档：`http://<host>:8010/api/docs`
- 数据库：命名卷 `kotone-data` 里的 `/data/kotone.db`；题库打进镜像
- 容器内部监听始终是 8000，**只改宿主机映射的端口**，不用动 Dockerfile

### 改端口

```bash
# 方式一（推荐，改一次永久生效）：项目根目录
cp .env.example .env
echo 'KOTONE_PORT=9000' >> .env      # 换成服务器上确认空闲的端口
docker compose up -d                  # 重建容器，端口立即生效

# 方式二（一次性）：
KOTONE_PORT=9000 docker compose up -d

# 检查端口是否空闲
ss -ltnp | grep :9000     # 没有输出就是空闲的
```

可用的环境变量（都写在根目录 `.env` 里）：

| 变量 | 默认 | 说明 |
| --- | --- | --- |
| `KOTONE_PORT` | `8010` | 宿主机映射端口 |
| `KOTONE_BIND` | `0.0.0.0` | 改成 `127.0.0.1` 则只允许本机访问（前面挂反代时用） |
| `KOTONE_EXAM_SIZE` | `10` | 每场考试抽题数 |
| `KOTONE_NAME` | `kotonego` | 容器名；同一台机器跑第二份实例（预发布/测试）时才需改 |

> 容器名可自定义意味着**同一台机器能同时跑多份**：比如生产 `.env` 用 `KOTONE_PORT=8010`，测试环境另一个目录用 `KOTONE_PORT=18010` + `KOTONE_NAME=kotone-staging`，两者互不干扰（已实测）。

### 更新版本

```bash
git pull
docker compose up -d --build     # 重建镜像并重启；数据库在命名卷里，不会丢
```

数据库表用 `CREATE TABLE IF NOT EXISTS`，改代码后直接重建即可，**不需要迁移脚本**。

---

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
| 题库 JSON（`backend/data/questions/`） | 本地运行时自动热加载（按文件 mtime）；Docker 下 `docker compose up -d --build`，或挂载目录后直接改文件即可 |
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

项目不内置证书。让容器只监听本机（`.env` 里 `KOTONE_BIND=127.0.0.1`），再用宿主机的 Caddy（最简）或 Nginx 反代到 `127.0.0.1:8010`。Caddy 两行配置：

```
learn.example.com {
    reverse_proxy 127.0.0.1:8010
}
```

单容器内前后端同源，因此不需要配置 CORS。

---

## GitHub Actions（自动构建 / 自动部署）

仓库里已经带了两个 workflow，推到分支即自动运行：

| 文件 | 触发 | 作用 |
| --- | --- | --- |
| `.github/workflows/ci.yml` | push / PR | 题库校验 + 后端冒烟测试 + `tsc` + 前端构建 |
| `.github/workflows/image.yml` | push 到 `main` / `python/0.0.1` | 构建镜像并推到 GHCR（amd64 + arm64） |

> 为什么在 CI 构建镜像：`npm ci` + Vite 构建峰值要几百 MB，在你那台小内存服务器上容易 OOM。
> CI 构建好之后，服务器只负责拉镜像，**零编译、不占内存**。

### 服务器使用 CI 构建的镜像

```bash
# 服务器上：.env 里指定镜像，不再本地构建
echo 'KOTONE_IMAGE=ghcr.io/yukiice/kotonego:latest' >> .env

# 首次使用（公开包，无需登录）
docker compose pull && docker compose up -d

# 之后每次发版git push后，在服务器执行：
docker compose pull && docker compose up -d
```

**关键一步**：GHCR 里新建的包默认是私有的，需要把包改成公开（否则服务器 pull 会 401）：
GitHub → 你的头像 → Your packages → `kotonego` → Package settings → Danger Zone → Change visibility → Public。
不想公开包也可以：在服务器上 `docker login ghcr.io`，用有 `read:packages` 权限的 PAT 登录一次（凭据会存在服务器上）。

> 注意：`docker compose up -d` 在本机没有该镜像时会**退回用 `build:` 段现场构建**。
> 所以顺序必须是先 `pull` 再 `up`；pull 失败时不要直接 `up`（小内存机器会当场 OOM）。
> 镜像在 GHCR 上是压缩传输的，服务器实际只下载约 **54 MB**（解压后磁盘占 271 MB）。

### 全自动部署（可选）

在仓库 Settings → Secrets and variables → Actions 里添加 3 个 secret：

| Secret | 内容 |
| --- | --- |
| `SSH_HOST` | 服务器 IP / 域名 |
| `SSH_USER` | 登录用户名（如 `root` 或 `ubuntu`） |
| `SSH_KEY` | 私钥全文（对应公钥已放进服务器 `~/.ssh/authorized_keys`） |

另外把 `image.yml` 里的 `cd "$HOME/KotoneGo"` 改成你服务器上的实际目录。之后每次 push 到这两个分支，
GitHub 会自动构建并远程执行 `git pull && docker compose pull && up -d`；不配 secret 则只构建镜像，不会连服务器。

### 回滚到某个提交

每个提交都会打一个不可变 tag（`sha-<前7位>`），`docker compose ps` 看不到也没关系，直接指定：

```bash
KOTONE_IMAGE=ghcr.io/yukiice/kotonego:sha-8ed6072 docker compose up -d
```

### 架构说明

默认构建 `linux/amd64` + `linux/arm64` 双架构（ARM 小鸡也能拉），代价是 arm64 那段在 QEMU 下跑
`npm ci` 会慢一些（首次约 10 分钟，有缓存后快）。如果服务器是普通 x86，把 `image.yml` 里
`platforms: linux/amd64,linux/arm64` 改成 `platforms: linux/amd64` 即可明显加速。

---

## 部署前端到 Vercel（可选）

> **Vercel 只能托管前端。** 后端需要常驻进程和可写磁盘（SQLite），Vercel 两者都没有；
> 要全站上 Vercel 就得把 `sqlite3` 换成 Postgres/Turso 并把 FastAPI 改写成 Serverless 函数，不建议。

**前提：后端必须能通过 HTTPS 访问** —— 浏览器禁止 HTTPS 页面请求 HTTP 接口（混合内容拦截）。
给 8010 套一层 HTTPS：Caddy 两行配置，或 Cloudflare Tunnel（免费、不用开端口）。

### 步骤

1. **Vercel 导入仓库**，Root Directory 填 `frontend`（`frontend/vercel.json` 已带好 Vite 配置和 SPA 回落）
2. **环境变量**：`VITE_API_BASE=https://api.你的域名`（构建时注入，改了要重新部署）
3. **后端放行跨域**（服务器 `.env`）：

```bash
KOTONE_CORS_ORIGINS=https://你的项目.vercel.app
# 预览域名每次不同，想一起放行再加一行正则：
KOTONE_CORS_ORIGIN_REGEX=^https://.*\.vercel\.app$
docker compose up -d        # 只改环境变量，不用重建镜像
```

4. 打开 Vercel 域名验证：首页、`/docs/11-oop`（刷新不能 404）、考试流程能提交。

### 代价

| 项 | 说明 |
| --- | --- |
| 两个域名 | 前端在 Vercel，接口在自己的服务器 |
| 要维护 CORS | 换域名/预览部署时得同步白名单 |
| 后端仍需服务器 | Vercel 解决不了数据存储 |
| 好处 | 前端走 CDN、全球加速、免费；服务器只跑接口，负载更小 |

如果只想要“一个域名、一套东西”，直接在服务器上用 Caddy 加域名更简单（见上一节），不必上 Vercel。
- 前端产物由后端托管，已开 gzip（主包 650KB → 220KB）与长缓存；**不要再另外起 nginx 或 `npm run dev`**

## 功能一览

| 页面 | 路径 | 说明 |
| --- | --- | --- |
| 首页 | `/` | 概览 + 快捷开始考试（题量 / 难度 / 主题可选，也可「只练错题」） |
| 语法文档 | `/docs` | 18 章 Markdown 教程，侧栏目录 + 搜索 + 本页 TOC + 手机端下拉切换 |
| 考试 | `/exam`、`/exam/:id` | 随机抽题，逐题作答，实时反馈，题目导航，进度服务端保存（可续答） |
| 成绩解析 | `/result/:id` | 分数环、各主题正确率、逐题解析、同范围再来一场 |
| 考试记录 | `/history` | 所有场次分数 / 用时 / 状态，可继续或删除 |
| 错题本 | `/wrong` | 错误次数、最后一次错误选项、错因、相关知识点、笔记、已掌握标记、按主题筛选；可导出 Markdown 或 Anki CSV |
| 题目反馈 | `/reports` | 查看「这题有问题」上报，按待处理 / 已修复筛选并标记状态 |
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

# 题库会按文件 mtime 自动热加载，改完 JSON 无需重启或 reload
# 如需强制刷新：curl -X POST http://127.0.0.1:8000/api/questions/reload

# 单元测试（先安装开发依赖）
cd backend && pip install -r requirements-dev.txt && python -m pytest -q

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
