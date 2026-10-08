# KotoneGo 生产镜像：单容器 = FastAPI(API) + 前端静态文件 + SQLite
#
# 两个阶段：
#   web  : 用 Node 把 React 打包成静态文件（Node 不进最终镜像）
#   runtime: 只装 Python 运行时依赖，体积小、内存占用低
#
# 构建 & 运行：
#   docker compose up -d --build      # 推荐
#   docker build -t kotonego:0.0.1 .  # 手动构建

# ---------- 阶段 1：构建前端 ----------
FROM node:22-alpine AS web
WORKDIR /web

# 先只拷依赖清单 → 依赖没变时构建缓存可复用，重复构建快很多
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund

COPY frontend/ ./
RUN npm run build

# ---------- 阶段 2：运行时 ----------
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    MALLOC_ARENA_MAX=2 \
    KOTONE_DB_PATH=/data/kotone.db

WORKDIR /app

# 单独一层装依赖 → 只改业务代码时不用重装 pip 包
COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install -r backend/requirements.txt

COPY backend/ ./backend/
COPY --from=web /web/dist ./backend/static

# 非 root 运行；/data 是 SQLite 数据卷挂载点
RUN useradd --create-home --uid 10001 app \
    && mkdir -p /data \
    && chown -R app:app /data /app
USER app

EXPOSE 8000

# 用 python 自带 urllib 做健康检查，不额外装 curl
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health', timeout=3)"

# workers=1 + 限制并发：小内存服务器上比多 worker 更稳（SQLite 也不需要多进程写）
CMD ["uvicorn", "app.main:app", \
     "--app-dir", "backend", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "1", \
     "--limit-concurrency", "64", \
     "--timeout-keep-alive", "10", \
     "--no-server-header"]
