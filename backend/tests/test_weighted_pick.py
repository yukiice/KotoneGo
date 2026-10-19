"""加权抽题：权重计算、无重复、以及偏向错题的统计效果。"""

from __future__ import annotations

import json
import random

import pytest

from app import service
from app.db import get_conn
from app.question_bank import load_questions


def _q(qid: str) -> dict:
    return {
        "id": qid,
        "topic": "basics",
        "question": f"题干 {qid}",
        "options": {"A": "a", "B": "b"},
        "answer": "A",
        "explanation": "解释",
    }


@pytest.fixture
def bank(bank_dir):
    items = [_q(f"basics-{i}") for i in range(1, 11)]
    (bank_dir / "01.json").write_text(json.dumps({"questions": items}), encoding="utf-8")
    load_questions()
    return bank_dir


def _set_stats(qid: str, attempts: int, correct: int) -> None:
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO question_stats (question_id, topic, attempts, correct_count, last_attempt_at) "
            "VALUES (?, 'basics', ?, ?, '')",
            (qid, attempts, correct),
        )


def test_weights_higher_for_low_accuracy(bank, tmp_db):
    _set_stats("basics-1", attempts=10, correct=10)  # 全对
    _set_stats("basics-2", attempts=10, correct=0)  # 全错
    pool = [load_questions()["basics-1"], load_questions()["basics-2"]]
    w_right, w_wrong = service._question_weights(pool)
    assert w_wrong > w_right


def test_unattempted_question_gets_neutral_weight(bank, tmp_db):
    pool = [load_questions()["basics-3"]]
    (weight,) = service._question_weights(pool)
    # 未作答按 0.5 正确率处理：1 + 0.5 = 1.5
    assert weight == pytest.approx(1.5)


def test_open_wrong_question_gets_bonus(bank, tmp_db):
    _set_stats("basics-4", attempts=2, correct=1)
    base = service._question_weights([load_questions()["basics-4"]])[0]
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO wrong_questions (question_id, topic, wrong_count, first_wrong_at, last_wrong_at, mastered) "
            "VALUES ('basics-4', 'basics', 1, '', '', 0)"
        )
    boosted = service._question_weights([load_questions()["basics-4"]])[0]
    assert boosted == pytest.approx(base + 0.5)


def test_weighted_pick_never_repeats_within_one_exam(bank, tmp_db):
    random.seed(0)
    for _ in range(50):
        picked = service.pick_questions(size=10, weighted=True)
        ids = [q.id for q in picked]
        assert len(ids) == len(set(ids)) == 10


def test_weighted_pick_size_capped_at_pool(bank, tmp_db):
    picked = service.pick_questions(size=999, weighted=True)
    assert len(picked) == 10


def test_weighted_pick_biases_toward_weak_questions(bank, tmp_db):
    """统计意义上：错得多的题被抽中的频率应明显高于全对的题。"""
    _set_stats("basics-1", attempts=20, correct=20)  # 全对，权重约 1.0
    _set_stats("basics-2", attempts=20, correct=0)  # 全错，权重约 2.0
    random.seed(12345)

    strong_hits = weak_hits = 0
    trials = 3000
    for _ in range(trials):
        ids = {q.id for q in service.pick_questions(size=1, weighted=True)}
        strong_hits += "basics-1" in ids
        weak_hits += "basics-2" in ids
    # 其余 8 题权重都是 1.5，只看这两题的相对比例：应明显偏向弱题
    assert weak_hits > strong_hits * 1.3


def test_unweighted_pick_unchanged_by_stats(bank, tmp_db):
    """默认 weighted=False 时，历史统计不应影响抽题，保持原有行为。"""
    _set_stats("basics-1", attempts=20, correct=0)
    random.seed(7)
    picked = service.pick_questions(size=10, weighted=False)
    assert len(picked) == 10


def test_create_exam_accepts_weighted(bank, tmp_db):
    exam = service.create_exam(size=5, weighted=True)
    assert len(exam["questions"]) == 5
