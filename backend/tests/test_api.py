"""HTTP 接口层测试：路由、状态码、请求校验、响应结构。

业务细节（加权、判分、回滚）已由 test_service / test_weighted_pick 覆盖，
这里只关心「接口对外的契约」是否稳定。使用临时题库 + 临时数据库。
"""

from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.question_bank import load_questions


def _q(qid: str, topic: str = "basics", answer: str = "A") -> dict:
    return {
        "id": qid,
        "topic": topic,
        "difficulty": "easy",
        "question": f"题干 {qid}",
        "options": {"A": "a", "B": "b", "C": "c"},
        "answer": answer,
        "explanation": f"解释 {qid}",
        "distractors": {"B": "B 为什么错", "C": "C 为什么错"},
    }


@pytest.fixture
def client(bank_dir, tmp_db):
    """4 道 basics 题 + 2 道 types 题，答案都是 A；数据库与题库都是临时的。"""
    items = [_q(f"basics-{i}") for i in range(1, 5)] + [_q(f"types-{i}", topic="types") for i in range(1, 3)]
    (bank_dir / "01.json").write_text(json.dumps({"questions": items}), encoding="utf-8")
    load_questions()
    # 使用 with 触发 lifespan（建表 + 校验题库），与真实启动路径一致
    with TestClient(app) as c:
        yield c


# --------------------------------------------------------------------------- #
# 元信息
# --------------------------------------------------------------------------- #
def test_health_reports_bank_size(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["question_count"] == 6


def test_meta_lists_topics(client):
    body = client.get("/api/meta").json()
    assert body["question_count"] == 6
    topic_ids = {t["topic"] for t in body["topics"]}
    assert {"basics", "types"} <= topic_ids


def test_reload_endpoint_returns_ok_for_valid_bank(client):
    body = client.post("/api/questions/reload").json()
    assert body == {"status": "ok", "question_count": 6}


# --------------------------------------------------------------------------- #
# 建题与请求校验
# --------------------------------------------------------------------------- #
def test_create_exam_default_size_is_capped_by_pool(client):
    resp = client.post("/api/exams", json={})
    assert resp.status_code == 200
    body = resp.json()
    # 默认 10 题，但题库只有 6 题，应返回全部 6 题且不重复
    assert len(body["questions"]) == 6
    assert len({q["id"] for q in body["questions"]}) == 6
    assert body["status"] == "in_progress"
    assert body["points_per_question"] > 0


def test_create_exam_with_weighted_flag(client):
    resp = client.post("/api/exams", json={"size": 3, "weighted": True})
    assert resp.status_code == 200
    assert len(resp.json()["questions"]) == 3


def test_create_exam_rejects_out_of_range_size(client):
    assert client.post("/api/exams", json={"size": 0}).status_code == 422
    assert client.post("/api/exams", json={"size": 61}).status_code == 422


def test_create_exam_rejects_unknown_difficulty(client):
    assert client.post("/api/exams", json={"difficulty": "impossible"}).status_code == 422


def test_create_exam_unknown_topic_returns_400(client):
    # ConflictError 在路由层统一映射为 400
    resp = client.post("/api/exams", json={"topics": ["no-such-topic"]})
    assert resp.status_code == 400
    assert "detail" in resp.json()


def test_create_exam_only_wrong_with_empty_book_returns_400(client):
    resp = client.post("/api/exams", json={"only_wrong": True})
    assert resp.status_code == 400


# --------------------------------------------------------------------------- #
# 作答 → 交卷 → 详情 → 历史 → 删除
# --------------------------------------------------------------------------- #
def _new_exam(client, size: int = 4) -> dict:
    resp = client.post("/api/exams", json={"size": size})
    assert resp.status_code == 200
    return resp.json()


def test_submit_correct_answer_returns_feedback(client):
    exam = _new_exam(client, size=2)
    qid = exam["questions"][0]["id"]

    resp = client.post(f"/api/exams/{exam['id']}/answers", json={"question_id": qid, "selected": "A"})
    assert resp.status_code == 200
    fb = resp.json()
    assert fb["is_correct"] is True
    assert fb["correct_answer"] == "A"
    assert fb["answered_count"] == 1
    assert fb["correct_count"] == 1


def test_submit_wrong_answer_adds_to_wrong_book(client):
    exam = _new_exam(client, size=2)
    qid = exam["questions"][0]["id"]

    resp = client.post(f"/api/exams/{exam['id']}/answers", json={"question_id": qid, "selected": "B"})
    assert resp.status_code == 200
    assert resp.json()["is_correct"] is False

    wrong = client.get("/api/wrong-questions").json()
    assert [w["question_id"] for w in wrong] == [qid]


def test_submit_with_unknown_option_returns_400(client):
    exam = _new_exam(client, size=2)
    qid = exam["questions"][0]["id"]
    resp = client.post(f"/api/exams/{exam['id']}/answers", json={"question_id": qid, "selected": "Z"})
    assert resp.status_code == 400


def test_submit_with_unknown_question_returns_404(client):
    exam = _new_exam(client, size=2)
    resp = client.post(f"/api/exams/{exam['id']}/answers", json={"question_id": "nope", "selected": "A"})
    assert resp.status_code == 404


def test_submit_question_not_in_exam_returns_404(client):
    exam = _new_exam(client, size=1)
    in_exam = {q["id"] for q in exam["questions"]}
    outside = next(qid for qid in load_questions() if qid not in in_exam)
    resp = client.post(f"/api/exams/{exam['id']}/answers", json={"question_id": outside, "selected": "A"})
    assert resp.status_code == 404


def test_submit_rejects_empty_selected(client):
    exam = _new_exam(client, size=1)
    qid = exam["questions"][0]["id"]
    resp = client.post(f"/api/exams/{exam['id']}/answers", json={"question_id": qid, "selected": ""})
    assert resp.status_code == 422


def test_submit_to_missing_exam_returns_404(client):
    qid = next(iter(load_questions()))
    resp = client.post("/api/exams/no-such-exam/answers", json={"question_id": qid, "selected": "A"})
    assert resp.status_code == 404


def test_finish_then_detail_and_history(client):
    exam = _new_exam(client, size=3)
    first, second = exam["questions"][0]["id"], exam["questions"][1]["id"]
    client.post(f"/api/exams/{exam['id']}/answers", json={"question_id": first, "selected": "A"})
    client.post(f"/api/exams/{exam['id']}/answers", json={"question_id": second, "selected": "C"})

    finish = client.post(f"/api/exams/{exam['id']}/finish")
    assert finish.status_code == 200
    result = finish.json()
    assert result["status"] == "finished"
    assert result["correct_count"] == 1
    # wrong_count = 题量 - 答对数：未作答的第 3 题交卷后也计为错误（按 0 分计）
    assert result["wrong_count"] == 2

    detail = client.get(f"/api/exams/{exam['id']}").json()
    assert len(detail["answers"]) == 3
    # 未作答的题在交卷后按 0 分计，selected 为空
    unanswered = [a for a in detail["answers"] if a["selected"] is None]
    assert len(unanswered) == 1

    history = client.get("/api/exams").json()
    assert [h["id"] for h in history] == [exam["id"]]


def test_history_limit_validation(client):
    assert client.get("/api/exams", params={"limit": 0}).status_code == 422
    assert client.get("/api/exams", params={"limit": 201}).status_code == 422


def test_get_missing_exam_returns_404(client):
    assert client.get("/api/exams/no-such-exam").status_code == 404


def test_finish_missing_exam_returns_404(client):
    assert client.post("/api/exams/no-such-exam/finish").status_code == 404


def test_delete_exam_then_gone(client):
    exam = _new_exam(client, size=1)
    assert client.delete(f"/api/exams/{exam['id']}").status_code == 204
    assert client.get(f"/api/exams/{exam['id']}").status_code == 404
    assert client.delete(f"/api/exams/{exam['id']}").status_code == 404


# --------------------------------------------------------------------------- #
# 错题本
# --------------------------------------------------------------------------- #
@pytest.fixture
def wrong_one(client):
    """做错一道题，返回其 question_id。"""
    exam = _new_exam(client, size=1)
    qid = exam["questions"][0]["id"]
    client.post(f"/api/exams/{exam['id']}/answers", json={"question_id": qid, "selected": "B"})
    return qid


def test_wrong_list_filter_by_topic(client, wrong_one):
    topic = load_questions()[wrong_one].topic
    other = "types" if topic == "basics" else "basics"

    assert len(client.get("/api/wrong-questions", params={"topic": topic}).json()) == 1
    assert client.get("/api/wrong-questions", params={"topic": other}).json() == []


def test_wrong_mark_mastered_and_filter(client, wrong_one):
    resp = client.patch(f"/api/wrong-questions/{wrong_one}", json={"mastered": True, "note": "记住了"})
    assert resp.status_code == 200
    item = resp.json()
    assert item["mastered"] is True
    assert item["note"] == "记住了"

    assert len(client.get("/api/wrong-questions", params={"mastered": True}).json()) == 1
    assert client.get("/api/wrong-questions", params={"mastered": False}).json() == []


def test_wrong_note_too_long_returns_422(client, wrong_one):
    resp = client.patch(f"/api/wrong-questions/{wrong_one}", json={"note": "x" * 2001})
    assert resp.status_code == 422


def test_wrong_patch_missing_returns_404(client):
    resp = client.patch("/api/wrong-questions/nope", json={"mastered": True})
    assert resp.status_code == 404


def test_wrong_delete_then_gone(client, wrong_one):
    assert client.delete(f"/api/wrong-questions/{wrong_one}").status_code == 204
    assert client.get("/api/wrong-questions").json() == []
    assert client.delete(f"/api/wrong-questions/{wrong_one}").status_code == 404


# --------------------------------------------------------------------------- #
# 统计
# --------------------------------------------------------------------------- #
def test_stats_shape_and_counts(client, wrong_one):
    body = client.get("/api/stats").json()
    assert body["bank_size"] == 6
    assert body["exam_count"] == 1
    assert body["wrong_open_count"] == 1
    assert body["wrong_mastered_count"] == 0
    assert isinstance(body["by_topic"], list)
    assert isinstance(body["recent_exams"], list)


def test_api_paths_do_not_fall_through_to_spa(client):
    # 未知 /api 路径必须是 404 JSON，而不是被前端 SPA 回落吞掉
    resp = client.get("/api/does-not-exist")
    assert resp.status_code == 404


# --------------------------------------------------------------------------- #
# 错题本导出
# --------------------------------------------------------------------------- #
def test_export_markdown_is_attachment(client, wrong_one):
    resp = client.get("/api/wrong-questions/export")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/markdown")
    disposition = resp.headers["content-disposition"]
    assert disposition.startswith("attachment; filename=\"kotone-wrong-book-")
    assert disposition.endswith(".md\"")
    assert "# KotoneGo 错题本" in resp.text
    assert "题目数量：1" in resp.text


def test_export_anki_is_csv_attachment(client, wrong_one):
    resp = client.get("/api/wrong-questions/export", params={"format": "anki"})
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/csv")
    assert resp.headers["content-disposition"].endswith(".csv\"")
    assert resp.text.startswith("#separator:comma\n")
    # 一道错题 = 一行数据
    data_lines = [line for line in resp.text.splitlines() if line and not line.startswith("#")]
    assert len(data_lines) == 1


def test_export_respects_mastered_filter(client, wrong_one):
    client.patch(f"/api/wrong-questions/{wrong_one}", json={"mastered": True})

    open_only = client.get("/api/wrong-questions/export", params={"mastered": False}).text
    assert "题目数量：0" in open_only
    mastered_only = client.get("/api/wrong-questions/export", params={"mastered": True}).text
    assert "题目数量：1" in mastered_only


def test_export_empty_book_still_downloads(client):
    resp = client.get("/api/wrong-questions/export")
    assert resp.status_code == 200
    assert "没有错题" in resp.text


def test_export_rejects_unknown_format(client):
    assert client.get("/api/wrong-questions/export", params={"format": "pdf"}).status_code == 422


def test_export_respects_topic_filter(client, wrong_one):
    topic = load_questions()[wrong_one].topic
    other = "types" if topic == "basics" else "basics"
    assert "题目数量：1" in client.get("/api/wrong-questions/export", params={"topic": topic}).text
    assert "题目数量：0" in client.get("/api/wrong-questions/export", params={"topic": other}).text
