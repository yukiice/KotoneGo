"""考试业务逻辑：抽题、判分、错题本、统计。

路由层只负责 HTTP，所有规则都在这里，方便单独测试。
"""

from __future__ import annotations

import json
import random
import sqlite3
import uuid
from datetime import datetime, timezone
from typing import Any

from .config import DEFAULT_EXAM_SIZE, POINTS_PER_QUESTION
from .db import get_conn
from .question_bank import Question, TOPIC_LABELS, load_questions


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


class NotFoundError(LookupError):
    pass


class ConflictError(RuntimeError):
    pass


# --------------------------------------------------------------------------- #
# 抽题
# --------------------------------------------------------------------------- #
def pick_questions(
    size: int = DEFAULT_EXAM_SIZE,
    topics: list[str] | None = None,
    difficulty: str = "any",
    only_wrong: bool = False,
) -> list[Question]:
    """随机抽题。

    规则：
      1. 先按主题 / 难度 / 错题本筛选候选池；
      2. 候选不足时，从剩余题目里补足（保证一定能凑满 size）；
      3. 题库总量不足 size 时，返回题库全部。
    """
    bank = load_questions()
    pool = list(bank.values())

    if only_wrong:
        with get_conn() as conn:
            rows = conn.execute("SELECT question_id FROM wrong_questions WHERE mastered = 0").fetchall()
        wrong_ids = {row["question_id"] for row in rows}
        pool = [q for q in pool if q.id in wrong_ids]

    if topics:
        topic_set = set(topics)
        pool = [q for q in pool if q.topic in topic_set]

    if difficulty != "any":
        filtered = [q for q in pool if q.difficulty == difficulty]
        # 若某个难度题量不够，就退回全部候选，避免空考卷
        pool = filtered or pool

    if not pool:
        raise ConflictError("没有符合条件（主题 / 难度 / 错题）的题目，请放宽筛选条件")

    size = max(1, min(size, len(pool)))
    return random.sample(pool, size)


# --------------------------------------------------------------------------- #
# 考试生命周期
# --------------------------------------------------------------------------- #
def create_exam(
    size: int = DEFAULT_EXAM_SIZE,
    topics: list[str] | None = None,
    difficulty: str = "any",
    only_wrong: bool = False,
) -> dict[str, Any]:
    questions = pick_questions(size=size, topics=topics, difficulty=difficulty, only_wrong=only_wrong)
    exam_id = uuid.uuid4().hex[:12]
    created_at = now_iso()

    with get_conn() as conn:
        conn.execute(
            "INSERT INTO exams (id, created_at, status, size, topics, score, correct_count) "
            "VALUES (?, ?, 'in_progress', ?, ?, 0, 0)",
            (exam_id, created_at, len(questions), json.dumps(topics or [], ensure_ascii=False)),
        )
        # 预先把题目顺序写进答案表（selected 为空表示未作答），这样刷新页面不丢题
        conn.executemany(
            "INSERT INTO exam_answers (exam_id, question_id, topic, selected, correct_answer, is_correct, answered_at) "
            "VALUES (?, ?, ?, '', ?, 0, '')",
            [(exam_id, q.id, q.topic, q.answer) for q in questions],
        )

    return get_exam(exam_id)


def _exam_row(conn: sqlite3.Connection, exam_id: str) -> sqlite3.Row:
    row = conn.execute("SELECT * FROM exams WHERE id = ?", (exam_id,)).fetchone()
    if row is None:
        raise NotFoundError(f"考试不存在: {exam_id}")
    return row


def _exam_result(row: sqlite3.Row, by_topic: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    return {
        "id": row["id"],
        "created_at": row["created_at"],
        "finished_at": row["finished_at"],
        "status": row["status"],
        "size": row["size"],
        "score": row["score"],
        "correct_count": row["correct_count"],
        "wrong_count": max(0, row["size"] - row["correct_count"]),
        "duration_seconds": row["duration_seconds"],
        "by_topic": by_topic or [],
    }


def get_exam(exam_id: str) -> dict[str, Any]:
    bank = load_questions()
    with get_conn() as conn:
        row = _exam_row(conn, exam_id)
        answer_rows = conn.execute(
            "SELECT * FROM exam_answers WHERE exam_id = ? ORDER BY id", (exam_id,)
        ).fetchall()

    answered = [r for r in answer_rows if r["selected"]]
    correct = [r for r in answer_rows if r["is_correct"]]
    score = _score(len(correct), row["size"])

    questions: list[dict[str, Any]] = []
    for answer_row in answer_rows:
        question = bank.get(answer_row["question_id"])
        if question is None:  # 题库被改过，跳过已删除的题
            continue
        payload = question.public()
        # 已经作答过的题带上结果，刷新页面后可以继续答剩下的
        payload["selected"] = answer_row["selected"] or None
        payload["is_correct"] = bool(answer_row["is_correct"]) if answer_row["selected"] else None
        questions.append(payload)

    return {
        "id": row["id"],
        "created_at": row["created_at"],
        "status": row["status"],
        "size": row["size"],
        "topics": json.loads(row["topics"] or "[]"),
        "points_per_question": POINTS_PER_QUESTION,
        "questions": questions,
        "answered_count": len(answered),
        "correct_count": len(correct),
        "score": score,
    }


def _score(correct_count: int, size: int) -> int:
    if size <= 0:
        return 0
    return round(correct_count / size * 100)


def submit_answer(exam_id: str, question_id: str, selected: str) -> dict[str, Any]:
    bank = load_questions()
    question = bank.get(question_id)
    if question is None:
        raise NotFoundError(f"题目不存在: {question_id}")
    if selected not in question.options:
        raise ConflictError(f"选项 {selected!r} 不在 {sorted(question.options)} 中")

    with get_conn() as conn:
        row = _exam_row(conn, exam_id)
        answer_row = conn.execute(
            "SELECT * FROM exam_answers WHERE exam_id = ? AND question_id = ?", (exam_id, question_id)
        ).fetchone()
        if answer_row is None:
            raise NotFoundError(f"这道题不属于本场考试: {question_id}")

        is_correct = selected == question.answer
        answered_at = now_iso()

        # 重复作答：先撤销上一次的统计影响，再按新答案重新计入，保证数据一致
        if answer_row["selected"]:
            _rollback_answer_stats(conn, question, bool(answer_row["is_correct"]))

        conn.execute(
            "UPDATE exam_answers SET selected = ?, is_correct = ?, answered_at = ? WHERE id = ?",
            (selected, int(is_correct), answered_at, answer_row["id"]),
        )
        _apply_question_stats(conn, question, is_correct, answered_at)
        if is_correct:
            _mark_mastered(conn, question.id)
        else:
            _upsert_wrong_question(conn, question, selected, answered_at)

        _refresh_exam_aggregate(conn, exam_id, row["size"])

    snapshot = get_exam(exam_id)
    return {
        "question_id": question_id,
        "selected": selected,
        "is_correct": is_correct,
        "correct_answer": question.answer,
        "explanation": question.explanation,
        "why_wrong": question.reason_for(selected),
        "knowledge": question.knowledge,
        "doc": question.doc,
        "topic": question.topic,
        "topic_label": TOPIC_LABELS.get(question.topic, question.topic),
        "question": question.question,
        "options": question.options,
        "answered_count": snapshot["answered_count"],
        "total": snapshot["size"],
        "correct_count": snapshot["correct_count"],
        "score": snapshot["score"],
    }


def _apply_question_stats(
    conn: sqlite3.Connection, question: Question, is_correct: bool, answered_at: str
) -> None:
    conn.execute(
        """
        INSERT INTO question_stats (question_id, topic, attempts, correct_count, last_attempt_at)
        VALUES (?, ?, 1, ?, ?)
        ON CONFLICT(question_id) DO UPDATE SET
            attempts = attempts + 1,
            correct_count = correct_count + excluded.correct_count,
            last_attempt_at = excluded.last_attempt_at
        """,
        (question.id, question.topic, int(is_correct), answered_at),
    )


def _rollback_answer_stats(conn: sqlite3.Connection, question: Question, was_correct: bool) -> None:
    """覆盖作答时，撤销上一次答案对统计与错题本的影响。"""
    conn.execute(
        "UPDATE question_stats SET attempts = MAX(attempts - 1, 0), "
        "correct_count = MAX(correct_count - ?, 0) WHERE question_id = ?",
        (int(was_correct), question.id),
    )
    if not was_correct:
        conn.execute(
            "UPDATE wrong_questions SET wrong_count = wrong_count - 1 WHERE question_id = ?",
            (question.id,),
        )
        conn.execute(
            "DELETE FROM wrong_questions WHERE question_id = ? AND wrong_count <= 0", (question.id,)
        )


def _mark_mastered(conn: sqlite3.Connection, question_id: str) -> None:
    """答对时自动把错题标记为“已掌握”（历史错误次数保留）。"""
    conn.execute(
        "UPDATE wrong_questions SET mastered = 1 WHERE question_id = ?", (question_id,)
    )


def _upsert_wrong_question(
    conn: sqlite3.Connection, question: Question, selected: str, answered_at: str
) -> None:
    conn.execute(
        """
        INSERT INTO wrong_questions
            (question_id, topic, wrong_count, last_selected, first_wrong_at, last_wrong_at, mastered, note)
        VALUES (?, ?, 1, ?, ?, ?, 0, '')
        ON CONFLICT(question_id) DO UPDATE SET
            wrong_count = wrong_count + 1,
            last_selected = excluded.last_selected,
            last_wrong_at = excluded.last_wrong_at,
            mastered = 0
        """,
        (question.id, question.topic, selected, answered_at, answered_at),
    )


def _refresh_exam_aggregate(conn: sqlite3.Connection, exam_id: str, size: int) -> None:
    row = conn.execute(
        "SELECT COALESCE(SUM(is_correct), 0) AS correct FROM exam_answers WHERE exam_id = ?", (exam_id,)
    ).fetchone()
    correct = int(row["correct"])
    conn.execute(
        "UPDATE exams SET correct_count = ?, score = ? WHERE id = ?",
        (correct, _score(correct, size), exam_id),
    )


def finish_exam(exam_id: str) -> dict[str, Any]:
    with get_conn() as conn:
        row = _exam_row(conn, exam_id)
        created = datetime.fromisoformat(row["created_at"])
        finished_at = now_iso()
        duration = max(0, int((datetime.fromisoformat(finished_at) - created).total_seconds()))
        conn.execute(
            "UPDATE exams SET status = 'finished', finished_at = ?, duration_seconds = ? WHERE id = ?",
            (finished_at, duration, exam_id),
        )
        _refresh_exam_aggregate(conn, exam_id, row["size"])
        by_topic = _exam_by_topic(conn, exam_id)
        row = _exam_row(conn, exam_id)

    return _exam_result(row, by_topic)


def _exam_by_topic(conn: sqlite3.Connection, exam_id: str) -> list[dict[str, Any]]:
    rows = conn.execute(
        "SELECT topic, COUNT(*) AS total, COALESCE(SUM(is_correct), 0) AS correct "
        "FROM exam_answers WHERE exam_id = ? GROUP BY topic ORDER BY topic",
        (exam_id,),
    ).fetchall()
    return [
        {
            "topic": row["topic"],
            "label": TOPIC_LABELS.get(row["topic"], row["topic"]),
            "total": row["total"],
            "correct": int(row["correct"]),
        }
        for row in rows
    ]


def get_exam_detail(exam_id: str) -> dict[str, Any]:
    bank = load_questions()
    with get_conn() as conn:
        row = _exam_row(conn, exam_id)
        answer_rows = conn.execute(
            "SELECT * FROM exam_answers WHERE exam_id = ? ORDER BY id", (exam_id,)
        ).fetchall()
        by_topic = _exam_by_topic(conn, exam_id)

    exam = _exam_result(row, by_topic)

    answers: list[dict[str, Any]] = []
    for answer_row in answer_rows:
        question = bank.get(answer_row["question_id"])
        if question is None:
            continue
        selected = answer_row["selected"] or None
        answers.append(
            {
                "question": question.public(),
                "selected": selected,
                "is_correct": bool(answer_row["is_correct"]) if selected else None,
                "correct_answer": question.answer,
                "explanation": question.explanation,
                "why_wrong": question.reason_for(selected) if selected else None,
                "knowledge": question.knowledge,
                "doc": question.doc,
            }
        )
    return {"exam": exam, "answers": answers}


def list_exams(limit: int = 50, offset: int = 0) -> list[dict[str, Any]]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM exams ORDER BY created_at DESC, rowid DESC LIMIT ? OFFSET ?", (limit, offset)
        ).fetchall()
    return [
        {
            "id": row["id"],
            "created_at": row["created_at"],
            "finished_at": row["finished_at"],
            "status": row["status"],
            "size": row["size"],
            "score": row["score"],
            "correct_count": row["correct_count"],
            "duration_seconds": row["duration_seconds"],
            "topics": json.loads(row["topics"] or "[]"),
        }
        for row in rows
    ]


def delete_exam(exam_id: str) -> None:
    with get_conn() as conn:
        _exam_row(conn, exam_id)  # 不存在会抛 404
        conn.execute("DELETE FROM exam_answers WHERE exam_id = ?", (exam_id,))
        conn.execute("DELETE FROM exams WHERE id = ?", (exam_id,))


# --------------------------------------------------------------------------- #
# 错题本
# --------------------------------------------------------------------------- #
def list_wrong_questions(topic: str | None = None, mastered: bool | None = None) -> list[dict[str, Any]]:
    bank = load_questions()
    sql = "SELECT * FROM wrong_questions WHERE 1 = 1"
    params: list[Any] = []
    if topic:
        sql += " AND topic = ?"
        params.append(topic)
    if mastered is not None:
        sql += " AND mastered = ?"
        params.append(int(mastered))
    sql += " ORDER BY mastered ASC, wrong_count DESC, last_wrong_at DESC"

    with get_conn() as conn:
        rows = conn.execute(sql, params).fetchall()

    items: list[dict[str, Any]] = []
    for row in rows:
        question = bank.get(row["question_id"])
        if question is None:
            continue
        selected = row["last_selected"]
        items.append(
            {
                "question_id": row["question_id"],
                "topic": row["topic"],
                "topic_label": TOPIC_LABELS.get(row["topic"], row["topic"]),
                "wrong_count": row["wrong_count"],
                "last_selected": selected,
                "first_wrong_at": row["first_wrong_at"],
                "last_wrong_at": row["last_wrong_at"],
                "mastered": bool(row["mastered"]),
                "note": row["note"],
                "question": question.public(),
                "correct_answer": question.answer,
                "explanation": question.explanation,
                "why_wrong": question.reason_for(selected) if selected else None,
                "knowledge": question.knowledge,
                "doc": question.doc,
            }
        )
    return items


def update_wrong_question(
    question_id: str, mastered: bool | None = None, note: str | None = None
) -> dict[str, Any]:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM wrong_questions WHERE question_id = ?", (question_id,)
        ).fetchone()
        if row is None:
            raise NotFoundError(f"错题本里没有这道题: {question_id}")
        if mastered is not None:
            conn.execute(
                "UPDATE wrong_questions SET mastered = ? WHERE question_id = ?",
                (int(mastered), question_id),
            )
        if note is not None:
            conn.execute("UPDATE wrong_questions SET note = ? WHERE question_id = ?", (note, question_id))

    for item in list_wrong_questions():
        if item["question_id"] == question_id:
            return item
    raise NotFoundError(question_id)


def delete_wrong_question(question_id: str) -> None:
    with get_conn() as conn:
        cur = conn.execute("DELETE FROM wrong_questions WHERE question_id = ?", (question_id,))
        if cur.rowcount == 0:
            raise NotFoundError(f"错题本里没有这道题: {question_id}")


# --------------------------------------------------------------------------- #
# 统计
# --------------------------------------------------------------------------- #
def get_stats() -> dict[str, Any]:
    bank = load_questions()
    with get_conn() as conn:
        exams = conn.execute("SELECT COUNT(*) AS c FROM exams").fetchone()["c"]
        finished = conn.execute("SELECT COUNT(*) AS c FROM exams WHERE status = 'finished'").fetchone()["c"]
        agg = conn.execute(
            "SELECT COUNT(*) AS attempts, COALESCE(SUM(is_correct), 0) AS correct "
            "FROM exam_answers WHERE selected != ''"
        ).fetchone()
        score_row = conn.execute(
            "SELECT COALESCE(AVG(score), 0) AS avg_score, COALESCE(MAX(score), 0) AS best, "
            "COALESCE(SUM(duration_seconds), 0) AS seconds FROM exams WHERE status = 'finished'"
        ).fetchone()
        attempts = int(agg["attempts"])
        correct = int(agg["correct"])

        topic_rows = conn.execute(
            "SELECT a.topic AS topic, COUNT(*) AS attempts, COALESCE(SUM(a.is_correct), 0) AS correct "
            "FROM exam_answers a WHERE a.selected != '' GROUP BY a.topic"
        ).fetchall()
        wrong_rows = conn.execute(
            "SELECT topic, SUM(CASE WHEN mastered = 0 THEN 1 ELSE 0 END) AS open_wrong, COUNT(*) AS total "
            "FROM wrong_questions GROUP BY topic"
        ).fetchall()

    topic_attempts = {row["topic"]: (int(row["attempts"]), int(row["correct"])) for row in topic_rows}
    wrong_by_topic = {row["topic"]: int(row["open_wrong"] or 0) for row in wrong_rows}

    bank_counts: dict[str, int] = {}
    for question in bank.values():
        bank_counts[question.topic] = bank_counts.get(question.topic, 0) + 1

    all_topics = sorted(set(bank_counts) | set(topic_attempts), key=lambda t: TOPIC_LABELS.get(t, t))
    by_topic = []
    for topic in all_topics:
        attempts_t, correct_t = topic_attempts.get(topic, (0, 0))
        by_topic.append(
            {
                "topic": topic,
                "label": TOPIC_LABELS.get(topic, topic),
                "attempts": attempts_t,
                "correct": correct_t,
                "accuracy": round(correct_t / attempts_t * 100, 1) if attempts_t else 0.0,
                "bank_count": bank_counts.get(topic, 0),
                "wrong_open": wrong_by_topic.get(topic, 0),
            }
        )

    wrong_open = sum(1 for item in list_wrong_questions(mastered=False))
    wrong_mastered = sum(1 for item in list_wrong_questions(mastered=True))

    return {
        "exam_count": int(exams),
        "finished_exam_count": int(finished),
        "answered_questions": attempts,
        "avg_score": round(float(score_row["avg_score"]), 1),
        "best_score": int(score_row["best"]),
        "total_minutes": round(float(score_row["seconds"]) / 60, 1),
        "bank_size": len(bank),
        "wrong_open_count": wrong_open,
        "wrong_mastered_count": wrong_mastered,
        "by_topic": by_topic,
        "recent_exams": list_exams(limit=10),
    }
