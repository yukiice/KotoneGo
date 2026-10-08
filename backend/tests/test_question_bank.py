"""题库加载：校验规则与 mtime 热加载。"""

from __future__ import annotations

import json
import os

import pytest

from app import question_bank
from app.question_bank import QuestionBankError, load_questions


def _q(qid: str, answer: str = "A", **extra) -> dict:
    base = {
        "id": qid,
        "topic": "basics",
        "question": "题干",
        "options": {"A": "a", "B": "b"},
        "answer": answer,
        "explanation": "解释",
    }
    base.update(extra)
    return base


def _write(qdir, name: str, questions: list[dict]) -> None:
    (qdir / name).write_text(json.dumps({"questions": questions}, ensure_ascii=False), encoding="utf-8")


def test_load_valid_bank(bank_dir):
    _write(bank_dir, "01-basics.json", [_q("basics-1"), _q("basics-2", answer="B")])
    bank = load_questions()
    assert set(bank) == {"basics-1", "basics-2"}
    assert bank["basics-2"].answer == "B"


def test_answer_not_in_options_is_rejected(bank_dir):
    _write(bank_dir, "01-basics.json", [_q("basics-1", answer="Z")])
    with pytest.raises(QuestionBankError, match="answer='Z'"):
        load_questions()


def test_duplicate_id_is_rejected(bank_dir):
    _write(bank_dir, "01-a.json", [_q("dup-1")])
    _write(bank_dir, "02-b.json", [_q("dup-1")])
    with pytest.raises(QuestionBankError, match="重复"):
        load_questions()


def test_missing_required_field_is_rejected(bank_dir):
    broken = _q("basics-1")
    del broken["explanation"]
    _write(bank_dir, "01-basics.json", [broken])
    with pytest.raises(QuestionBankError, match="缺少字段"):
        load_questions()


def test_invalid_difficulty_is_rejected(bank_dir):
    _write(bank_dir, "01-basics.json", [_q("basics-1", difficulty="impossible")])
    with pytest.raises(QuestionBankError, match="difficulty"):
        load_questions()


def test_distractor_for_unknown_option_is_rejected(bank_dir):
    _write(bank_dir, "01-basics.json", [_q("basics-1", distractors={"Z": "不存在"})])
    with pytest.raises(QuestionBankError, match="distractors"):
        load_questions()


def test_empty_directory_is_rejected(bank_dir):
    with pytest.raises(QuestionBankError, match="没有任何 .json"):
        load_questions()


def test_hot_reload_picks_up_file_change(bank_dir):
    path = bank_dir / "01-basics.json"
    _write(bank_dir, "01-basics.json", [_q("basics-1")])
    assert set(load_questions()) == {"basics-1"}

    # 修改文件并强制推进 mtime，避免文件系统时间精度导致判断不出变化
    _write(bank_dir, "01-basics.json", [_q("basics-1"), _q("basics-2")])
    stat = path.stat()
    os.utime(path, ns=(stat.st_atime_ns, stat.st_mtime_ns + 1_000_000_000))

    assert set(load_questions()) == {"basics-1", "basics-2"}


def test_hot_reload_new_file_is_detected(bank_dir):
    _write(bank_dir, "01-basics.json", [_q("basics-1")])
    assert len(load_questions()) == 1
    _write(bank_dir, "02-more.json", [_q("more-1")])
    assert set(load_questions()) == {"basics-1", "more-1"}


def test_bad_edit_keeps_error_and_does_not_poison_cache(bank_dir):
    """改坏 JSON 时应抛错；修复后应恢复正常，而不是永久卡在错误状态。"""
    path = bank_dir / "01-basics.json"
    _write(bank_dir, "01-basics.json", [_q("basics-1")])
    assert len(load_questions()) == 1

    path.write_text("{ not json", encoding="utf-8")
    stat = path.stat()
    os.utime(path, ns=(stat.st_atime_ns, stat.st_mtime_ns + 1_000_000_000))
    with pytest.raises(QuestionBankError):
        load_questions()

    _write(bank_dir, "01-basics.json", [_q("basics-1"), _q("basics-2")])
    stat = path.stat()
    os.utime(path, ns=(stat.st_atime_ns, stat.st_mtime_ns + 2_000_000_000))
    assert set(load_questions()) == {"basics-1", "basics-2"}


def test_reload_questions_forces_reread(bank_dir):
    _write(bank_dir, "01-basics.json", [_q("basics-1")])
    load_questions()
    question_bank._cache["bank"] = None  # 模拟外部清缓存
    assert set(question_bank.reload_questions()) == {"basics-1"}


def test_real_bank_is_valid():
    """仓库自带的真实题库必须能通过校验（防止提交坏题）。"""
    bank = question_bank._read_bank()
    assert len(bank) > 0
    topics = {q.topic for q in bank.values()}
    missing_labels = topics - set(question_bank.TOPIC_LABELS)
    assert not missing_labels, f"这些主题缺少中文名: {missing_labels}"
