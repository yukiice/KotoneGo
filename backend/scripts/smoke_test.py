"""端到端冒烟测试：不需要 pytest，直接用标准库跑一遍完整流程。

用法（先启动后端）：
    python3 scripts/smoke_test.py
或指定地址：
    KOTONE_BASE=http://127.0.0.1:8000 python3 scripts/smoke_test.py
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request

BASE = os.getenv("KOTONE_BASE", "http://127.0.0.1:8000")


def call(method: str, path: str, payload: dict | None = None) -> object:
    data = json.dumps(payload).encode() if payload is not None else None
    request = urllib.request.Request(
        f"{BASE}{path}",
        data=data,
        method=method,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            body = response.read().decode()
            return json.loads(body) if body else None
    except urllib.error.HTTPError as exc:
        raise SystemExit(f"[FAIL] {method} {path} -> {exc.code} {exc.read().decode()}") from exc


def main() -> int:
    health = call("GET", "/api/health")
    print(f"[OK] health: {health}")

    exam = call("POST", "/api/exams", {"size": 10})
    assert isinstance(exam, dict)
    questions = exam["questions"]
    assert len(questions) == 10, "应该抽到 10 道题"
    assert all("answer" not in q for q in questions), "未作答前不能下发答案"
    print(f"[OK] 创建考试 {exam['id']}，题量 {len(questions)}")

    # 第一题故意答错，其余按“随便选一个”作答，验证反馈结构
    first = questions[0]
    wrong_key = next(key for key in first["options"] if key != "A")
    feedback = call("POST", f"/api/exams/{exam['id']}/answers", {"question_id": first["id"], "selected": wrong_key})
    assert isinstance(feedback, dict)
    assert "correct_answer" in feedback and feedback["explanation"], "必须返回答案与解析"
    print(f"[OK] 提交答案 -> {'正确' if feedback['is_correct'] else '错误'}，正确答案 {feedback['correct_answer']}")

    for question in questions[1:]:
        call("POST", f"/api/exams/{exam['id']}/answers", {"question_id": question["id"], "selected": "A"})

    result = call("POST", f"/api/exams/{exam['id']}/finish")
    assert isinstance(result, dict)
    print(f"[OK] 交卷：得分 {result['score']}，正确 {result['correct_count']}，用时 {result['duration_seconds']}s")

    detail = call("GET", f"/api/exams/{exam['id']}")
    assert isinstance(detail, dict) and len(detail["answers"]) == 10
    print(f"[OK] 考试详情：{len(detail['answers'])} 条作答记录")

    wrong = call("GET", "/api/wrong-questions?mastered=false")
    print(f"[OK] 错题本待攻克 {len(wrong)} 题")

    if wrong:
        target = wrong[0]["question_id"]
        updated = call("PATCH", f"/api/wrong-questions/{target}", {"mastered": True, "note": "冒烟测试"})
        assert isinstance(updated, dict) and updated["mastered"] is True
        call("PATCH", f"/api/wrong-questions/{target}", {"mastered": False, "note": ""})
        print("[OK] 错题标记与笔记更新")

    stats = call("GET", "/api/stats")
    assert isinstance(stats, dict)
    print(f"[OK] 统计：考试 {stats['exam_count']} 场，作答 {stats['answered_questions']} 题，平均分 {stats['avg_score']}")

    history = call("GET", "/api/exams?limit=5")
    assert isinstance(history, list)
    print(f"[OK] 历史记录 {len(history)} 条")

    print("\n全部冒烟测试通过 ✅")
    return 0


if __name__ == "__main__":
    sys.exit(main())
