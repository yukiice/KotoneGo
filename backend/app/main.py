"""FastAPI 应用入口。

两种运行方式（同一份代码）：

1. 本地开发：前后端分离
       cd backend
       python3 -m venv .venv && source .venv/bin/activate
       pip install -r requirements.txt
       uvicorn app.main:app --reload --port 8000
   接口文档：http://127.0.0.1:8000/api/docs

2. 生产 / Docker：单进程同时提供 API 和前端页面
   把 `frontend/dist` 放到 `backend/static/`（Dockerfile 已自动完成），
   访问 http://<host>:8000 即是完整的网站；`/api/*` 是接口。
   注意：Swagger 文档在 `/api/docs`，因为 `/docs` 被站内的「语法文档」页面占用了。
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .config import CORS_ORIGINS, DEFAULT_EXAM_SIZE, POINTS_PER_QUESTION, STATIC_DIR
from .db import init_db
from .question_bank import QuestionBankError, load_questions, reload_questions, topic_summary
from .routers import exams, stats


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """启动时建库建表并校验题库，坏数据直接让进程失败（而不是等到用户点开才报错）。"""
    init_db()
    load_questions()
    yield


app = FastAPI(
    title="KotoneGo Python 学习平台 API",
    description="面向 React/TS 前端开发者的 Python 语法学习 + 考试系统后端。",
    version="0.0.1",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url=None,
    openapi_url="/api/openapi.json",
)

# 压缩 JSON / JS / CSS / Markdown，明显省流量（前端主包 650KB → 220KB）
app.add_middleware(GZipMiddleware, minimum_size=1024)

# 本地开发时前端在 5173，需要允许跨域；单容器部署时前后端同源，用不上
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(exams.router)
app.include_router(stats.router)


@app.middleware("http")
async def _cache_headers(request: Request, call_next):
    """Vite 产物文件名带内容哈希 → 可以长缓存；HTML 每次校验，避免发版后拿到旧页面。"""
    response = await call_next(request)
    path = request.url.path
    if path.startswith("/assets/") and response.status_code == 200:
        response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
    elif response.headers.get("content-type", "").startswith("text/html"):
        response.headers["Cache-Control"] = "no-cache"
    return response


@app.get("/api/health", tags=["meta"], summary="健康检查")
def health() -> dict:
    bank = load_questions()
    return {"status": "ok", "question_count": len(bank), "default_exam_size": DEFAULT_EXAM_SIZE}


@app.get("/api/meta", tags=["meta"], summary="题库元信息（主题、题量、分值）")
def meta() -> dict:
    bank = load_questions()
    return {
        "question_count": len(bank),
        "default_exam_size": DEFAULT_EXAM_SIZE,
        "points_per_question": POINTS_PER_QUESTION,
        "topics": topic_summary(),
    }


@app.post("/api/questions/reload", tags=["meta"], summary="重新加载题库 JSON（免重启）")
def reload_bank() -> dict:
    try:
        bank = reload_questions()
    except QuestionBankError as exc:
        return {"status": "error", "detail": str(exc)}
    return {"status": "ok", "question_count": len(bank)}


# ---------------------------------------------------------------------------
# 前端静态托管（只有存在构建产物时才挂载，本地开发不受影响）
# ---------------------------------------------------------------------------

if STATIC_DIR.is_dir():
    _index = STATIC_DIR / "index.html"
    _assets = STATIC_DIR / "assets"
    _root = STATIC_DIR.resolve()

    if _assets.is_dir():
        app.mount("/assets", StaticFiles(directory=_assets), name="assets")

    @app.get("/{path:path}", include_in_schema=False)
    async def spa(path: str) -> FileResponse:
        """SPA 回落：真实文件优先，其余交给 React Router（刷新 /docs/11-oop 也能用）。"""
        if path.startswith("api/"):
            raise HTTPException(status_code=404, detail="接口不存在")
        target = (_root / path).resolve()
        if path and target.is_file() and target.is_relative_to(_root):
            return FileResponse(target)
        if "." in Path(path).name:  # 缺图片/字体等静态文件时不要回落到 HTML
            raise HTTPException(status_code=404, detail="文件不存在")
        return FileResponse(_index)
