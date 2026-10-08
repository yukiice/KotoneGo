"""考试业务逻辑边界：抽题、判分、重复作答回滚、错题本。

使用临时题库 + 临时数据库，结果可预测。
"""

from __future__ import annotations

import json

import pytest

from app import service
from app.question_bank import load_questions
from app.service import ConflictError, NotFoundError


def _q(qid: str, topic: str = "basics", answer: str = "A", difficulty: str = "easy") -> dict:
    return {
        "id": qid,
        "topic": topic,
        "difficulty": difficulty,
        "question": f"题干 {qid}",
        "options": {"A": "a", "B": "b", "C": "c"},
        "answer": answer,
        "explanation": f"解释 {qid}",
        "distractors": {"B": "B 为什么错", "C": "C 为什么错"},
    }


@pytest.fixture
def bank(bank_dir):
    """4 道 basics 题 + 2 道 types 题，答案都是 A（便于控制对错）。"""
    items = [_q(f"basics-{i}") for i in range(1, 5)] + [_q(f"types-{i}", topic="types") for i in range(1, 3)]
    (bank_dir / "01.json").write_text(json.dumps({"questions": items}), encoding="utf-8")
    load_questions()
    return bank_dir


# --------------------------------------------------------------------------- #
# 抽题边界
# --------------------------------------------------------------------------- #
def test_pick_respects_size(bank, tmp_db):
    picked = service.pick_questions(size=3)
    assert len(picked) == 3
    assert len({q.id for q in picked}) == 3  # 不重复


def test_pick_caps_size_at_pool(bank, tmp_db):
    picked = service.pick_questions(size=999)
    assert len(picked) == 6


def test_pick_filters_by_topic(bank, tmp_db):
    picked = service.pick_questions(size=10, topics=["types"])
    assert {q.topic for q in picked} == {"types"}
    assert len(picked) == 2


def test_pick_empty_topic_raises_conflict(bank, tmp_db):
    with pytest.raises(ConflictError):
        service.pick_questions(size=3, topics=["no-such-topic"])


def test_pick_only_wrong_with_empty_wrong_book_raises(bank, tmp_db):
    with pytest.raises(ConflictError):
        service.pick_questions(size=3, only_wrong=True)


def test_pick_only_wrong_returns_open_wrong_questions(bank, tmp_db):
    exam = service.create_exam(size=6)
    wrong_qids = [q["id"] for q in exam["questions"]][:2]
    for qid in wrong_qids:
        service.submit_answer(exam["id"], qid, "B")  # 故意答错

    picked = service.pick_questions(size=10, only_wrong=True)
    assert {q.id for q in picked} == set(wrong_qids)


def test_difficulty_falls_back_when_no_match(bank, tmp_db):
    # 库里全是 easy，请求 hard 时应退回全部候选，而不是返回空卷
    picked = service.pick_questions(size=3, difficulty="hard")
    assert len(picked) == 3


# --------------------------------------------------------------------------- #
# 判分与分数
# --------------------------------------------------------------------------- #
def test_score_rounding():
    assert service._score(0, 10) == 0
    assert service._score(3, 10) == 30
    assert service._score(1, 3) == 33  # 33.33 -> 33
    assert service._score(2, 3) == 67  # 66.67 -> 67
    assert service._score(0, 0) == 0  # 防除零


def test_create_exam_does_not_leak_answers(bank, tmp_db):
    exam = service.create_exam(size=3)
    assert len(exam["questions"]) == 3
    for question in exam["questions"]:
        assert "answer" not in question
        assert "explanation" not in question


def test_submit_correct_and_finish_score(bank, tmp_db):
    exam = service.create_exam(size=4)
    qids = [q["id"] for q in exam["questions"]]
    for qid in qids[:3]:
        assert service.submit_answer(exam["id"], qid, "A")["is_correct"] is True
    service.submit_answer(exam["id"], qids[3], "B")

    result = service.finish_exam(exam["id"])
    assert result["correct_count"] == 3
    assert result["score"] == 75
    assert result["status"] == "finished"


def test_submit_wrong_answer_returns_reason(bank, tmp_db):
    exam = service.create_exam(size=1)
    qid = exam["questions"][0]["id"]
    res = service.submit_answer(exam["id"], qid, "B")
    assert res["is_correct"] is False
    assert res["correct_answer"] == "A"
    assert res["why_wrong"] == "B 为什么错"


def test_submit_rejects_invalid_option(bank, tmp_db):
    exam = service.create_exam(size=1)
    qid = exam["questions"][0]["id"]
    with pytest.raises(ConflictError):
        service.submit_answer(exam["id"], qid, "Z")


def test_submit_rejects_question_not_in_exam(bank, tmp_db):
    # 先创建一场只含 1 题的考试，再尝试提交库中存在、但不属于这场考试的题
    exam = service.create_exam(size=1)
    in_exam = exam["questions"][0]["id"]
    outside = next(qid for qid in load_questions() if qid != in_exam)
    with pytest.raises(NotFoundError, match="不属于本场考试"):
        service.submit_answer(exam["id"], outside, "A")


def test_submit_rejects_unknown_exam(bank, tmp_db):
    exam = service.create_exam(size=1)
    with pytest.raises(NotFoundError):
        service.submit_answer("no-such-exam", exam["questions"][0]["id"], "A")


# --------------------------------------------------------------------------- #
# 重复作答回滚（最容易出静默错误的地方）
# --------------------------------------------------------------------------- #
def test_resubmit_wrong_then_correct_rolls_back_wrong_book(bank, tmp_db):
    exam = service.create_exam(size=1)
    qid = exam["questions"][0]["id"]

    service.submit_answer(exam["id"], qid, "B")  # 先答错
    wrong = {w["question_id"]: w for w in service.list_wrong_questions()}
    assert wrong[qid]["wrong_count"] == 1
    assert wrong[qid]["mastered"] is False

    service.submit_answer(exam["id"], qid, "A")  # 改答对
    # 改答对后回滚了错误次数：错题本中该题的 wrong_count 应为 0（被删除或清零）
    wrong = {w["question_id"]: w for w in service.list_wrong_questions()}
    assert qid not in wrong or wrong[qid]["wrong_count"] == 0

    stats = service.get_stats()
    assert stats["answered_questions"] == 1  # 只算一次作答，不能因为改答而翻倍
    assert sum(t["correct"] for t in stats["by_topic"]) == 1


def test_resubmit_does_not_double_count_attempts(bank, tmp_db):
    exam = service.create_exam(size=1)
    qid = exam["questions"][0]["id"]
    for _ in range(3):
        service.submit_answer(exam["id"], qid, "B")
    stats = service.get_stats()
    assert stats["answered_questions"] == 1
    wrong = {w["question_id"]: w for w in service.list_wrong_questions()}
    assert wrong[qid]["wrong_count"] == 1  # 同一场同一题重复答错只计 1 次


def test_correct_answer_marks_wrong_question_mastered(bank, tmp_db):
    first = service.create_exam(size=1)
    qid = first["questions"][0]["id"]
    service.submit_answer(first["id"], qid, "B")

    # 下一场考试中答对同一题 -> 标记已掌握，但保留错误历史
    second = service.create_exam(size=6)
    assert qid in {q["id"] for q in second["questions"]}
    service.submit_answer(second["id"], qid, "A")

    item = {w["question_id"]: w for w in service.list_wrong_questions()}[qid]
    assert item["mastered"] is True
    assert item["wrong_count"] == 1


def test_delete_exam_removes_answers(bank, tmp_db):
    exam = service.create_exam(size=2)
    service.delete_exam(exam["id"])
    with pytest.raises(NotFoundError):
        service.get_exam(exam["id"])
    with pytest.raises(NotFoundError):
        service.delete_exam(exam["id"])


def test_update_and_delete_wrong_question(bank, tmp_db):
    exam = service.create_exam(size=1)
    qid = exam["questions"][0]["id"]
    service.submit_answer(exam["id"], qid, "B")

    updated = service.update_wrong_question(qid, note="记住 is 与 ==")
    assert updated["note"] == "记住 is 与 =="

    service.delete_wrong_question(qid)
    with pytest.raises(NotFoundError):
        service.delete_wrong_question(qid)
