"""SQLite 数据层。

刻意使用标准库 sqlite3，避免额外依赖，也方便初学者直接看懂 SQL。
表结构：
  exams           每次考试（一次作答会话）
  exam_answers    考试里每道题的作答记录
  question_stats  每道题的历史正确率（用于统计与智能选“薄弱题”）
  wrong_questions 错题本（一道题一行，累计错误次数）
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from typing import Iterator

from .config import DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS exams (
    id               TEXT PRIMARY KEY,
    created_at       TEXT NOT NULL,
    finished_at      TEXT,
    status           TEXT NOT NULL DEFAULT 'in_progress',
    size             INTEGER NOT NULL,
    topics           TEXT NOT NULL DEFAULT '[]',
    score            INTEGER NOT NULL DEFAULT 0,
    correct_count    INTEGER NOT NULL DEFAULT 0,
    duration_seconds INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS exam_answers (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    exam_id        TEXT NOT NULL REFERENCES exams(id) ON DELETE CASCADE,
    question_id    TEXT NOT NULL,
    topic          TEXT NOT NULL,
    selected       TEXT NOT NULL,
    correct_answer TEXT NOT NULL,
    is_correct     INTEGER NOT NULL,
    answered_at    TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_exam_answers_exam ON exam_answers(exam_id);

CREATE TABLE IF NOT EXISTS question_stats (
    question_id     TEXT PRIMARY KEY,
    topic           TEXT NOT NULL,
    attempts        INTEGER NOT NULL DEFAULT 0,
    correct_count   INTEGER NOT NULL DEFAULT 0,
    last_attempt_at TEXT
);

CREATE TABLE IF NOT EXISTS wrong_questions (
    question_id   TEXT PRIMARY KEY,
    topic         TEXT NOT NULL,
    wrong_count   INTEGER NOT NULL DEFAULT 1,
    last_selected TEXT,
    first_wrong_at TEXT NOT NULL,
    last_wrong_at  TEXT NOT NULL,
    mastered      INTEGER NOT NULL DEFAULT 0,
    note          TEXT NOT NULL DEFAULT ''
);
"""


def init_db() -> None:
    """建库建表，幂等，可以在每次启动时调用。"""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with connect() as conn:
        conn.executescript(SCHEMA)


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, timeout=15)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


@contextmanager
def get_conn() -> Iterator[sqlite3.Connection]:
    conn = connect()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
