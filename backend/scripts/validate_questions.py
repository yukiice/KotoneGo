"""校验题库 JSON：用法 python3 scripts/validate_questions.py"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.question_bank import QuestionBankError, load_questions, topic_summary  # noqa: E402


def main() -> int:
    try:
        bank = load_questions()
    except QuestionBankError as exc:
        print(f"[FAIL] {exc}")
        return 1

    print(f"[OK] 共 {len(bank)} 道题")
    for item in topic_summary():
        print(f"  - {item['topic']:<14} {item['label']:<16} {item['count']:>4} 题")

    short = [q.id for q in bank.values() if not q.explanation.strip()]
    if short:
        print(f"[WARN] 以下题目缺少解析: {short}")
    no_doc = [q.id for q in bank.values() if not q.doc]
    if no_doc:
        print(f"[WARN] 以下题目没有关联文档章节: {len(no_doc)} 题")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
