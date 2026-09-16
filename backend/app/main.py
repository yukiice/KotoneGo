"""FastAPI 应用入口。

本地启动：
    cd backend
    python3 -m venv .venv && source .venv/bin/activate
    pip install -r requirements.txt
    uvicorn app.main:app --reload --port 8000

接口文档：http://127.0.0.1:8000/docs
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import CORS_ORIGINS, DEFAULT_EXAM_SIZE, POINTS_PER_QUESTION
from .db import init_db
from .question_bank import QuestionBankError, load_questions, reload_questions, topic_summary
from .routers import exams, stats

app = FastAPI(
    title="KotoneGo Python 学习平台 API",
    description="面向 React/TS 前端开发者的 Python 语法学习 + 考试系统后端。",
    version="0.0.1",
)

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


@app.on_event("startup")
def _startup() -> None:
    init_db()
    load_questions()  # 启动即校验题库，坏数据直接报错


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


@app.post("/api/questions/reload", tags=["meta"], summary="重新加载题库 JSON（开发用，免重启）")
def reload_bank() -> dict:
    try:
        bank = reload_questions()
    except QuestionBankError as exc:
        return {"status": "error", "detail": str(exc)}
    return {"status": "ok", "question_count": len(bank)}
