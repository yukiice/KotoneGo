"""测试公共夹具。

每个测试都使用独立的临时 SQLite 文件，不会碰到真实的 data/kotone.db。
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app import db, question_bank  # noqa: E402


@pytest.fixture
def tmp_db(tmp_path, monkeypatch):
    """把数据库指向临时文件并建表。"""
    path = tmp_path / "test.db"
    monkeypatch.setattr(db, "DB_PATH", path)
    db.init_db()
    return path


@pytest.fixture
def bank_dir(tmp_path, monkeypatch):
    """提供一个可写的临时题库目录，并让 question_bank 指向它。"""
    qdir = tmp_path / "questions"
    qdir.mkdir()
    monkeypatch.setattr(question_bank, "QUESTIONS_DIR", qdir)
    monkeypatch.setitem(question_bank._cache, "bank", None)
    monkeypatch.setitem(question_bank._cache, "signature", None)
    return qdir
