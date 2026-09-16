"""全局配置。

所有路径都基于本文件的位置推导，因此无论从哪个目录启动 uvicorn 都能工作。
"""

from __future__ import annotations

import os
from pathlib import Path

# backend/app/config.py -> backend/
BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"
QUESTIONS_DIR = DATA_DIR / "questions"
DB_PATH = Path(os.getenv("KOTONE_DB_PATH", DATA_DIR / "kotone.db"))

# 前端构建产物目录（Docker 镜像会把 frontend/dist 放到这里，由 FastAPI 直接托管）。
# 本地开发时这个目录不存在，前后端分离跑（Vite 5173 + 本服务 8000），互不影响。
STATIC_DIR = Path(os.getenv("KOTONE_STATIC_DIR", BASE_DIR / "static"))

# 每场考试默认题量、可选范围与每题分值（题量 * 分值 = 100 分）
DEFAULT_EXAM_SIZE = int(os.getenv("KOTONE_EXAM_SIZE", "10"))
MIN_EXAM_SIZE = 1
MAX_EXAM_SIZE = 60
POINTS_PER_QUESTION = 10

# 允许前端跨域访问（本地开发时 Vite 默认跑在 5173）
CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "KOTONE_CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173,"
        "http://localhost:4173,http://127.0.0.1:4173",
    ).split(",")
    if origin.strip()
]
