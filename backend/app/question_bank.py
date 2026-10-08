"""题库加载与校验。

题库是 data/questions/*.json，一个文件一个主题，方便按主题增补。
任何格式错误都会在启动时抛错，避免“坏题”悄悄进入考试。
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .config import QUESTIONS_DIR

REQUIRED_FIELDS = {"id", "topic", "question", "options", "answer", "explanation"}
VALID_DIFFICULTIES = {"easy", "medium", "hard"}

# 主题中文名，前端展示用；新增主题时在这里补一条
TOPIC_LABELS: dict[str, str] = {
    "basics": "基础语法与变量",
    "types": "数据类型与转换",
    "operators": "运算符与表达式",
    "strings": "字符串处理",
    "collections": "列表/元组/字典/集合",
    "control": "条件与循环",
    "functions": "函数与作用域",
    "comprehensions": "推导式",
    "iterators": "迭代器与生成器",
    "oop": "面向对象",
    "exceptions": "异常处理",
    "modules": "模块、包与标准库",
    "files": "文件与数据格式",
    "typing": "类型注解与 mypy",
    "decorators": "闭包与装饰器",
    "async": "异步编程",
    "pitfalls": "易错点与 JS/TS 对比",
}


class QuestionBankError(RuntimeError):
    """题库格式错误。"""


@dataclass(frozen=True)
class Question:
    id: str
    topic: str
    question: str
    options: dict[str, str]
    answer: str
    explanation: str
    difficulty: str = "easy"
    distractors: dict[str, str] = field(default_factory=dict)
    knowledge: list[str] = field(default_factory=list)
    doc: str = ""
    tags: list[str] = field(default_factory=list)

    def reason_for(self, selected: str) -> str | None:
        """返回某个错误选项的原因说明；没有写就返回 None。"""
        if selected == self.answer:
            return None
        return self.distractors.get(selected)

    def public(self) -> dict[str, Any]:
        """下发给前端的“无答案”版本。"""
        return {
            "id": self.id,
            "topic": self.topic,
            "topic_label": TOPIC_LABELS.get(self.topic, self.topic),
            "difficulty": self.difficulty,
            "question": self.question,
            "options": self.options,
        }

    def revealed(self) -> dict[str, Any]:
        """答完之后才下发的“带答案”版本。"""
        data = self.public()
        data.update(
            {
                "answer": self.answer,
                "explanation": self.explanation,
                "distractors": self.distractors,
                "knowledge": self.knowledge,
                "doc": self.doc,
                "tags": self.tags,
            }
        )
        return data


def _validate(raw: dict[str, Any], source: Path) -> Question:
    missing = REQUIRED_FIELDS - raw.keys()
    if missing:
        raise QuestionBankError(f"{source.name}: 题目 {raw.get('id')} 缺少字段 {sorted(missing)}")

    options = raw["options"]
    if not isinstance(options, dict) or len(options) < 2:
        raise QuestionBankError(f"{source.name}: 题目 {raw['id']} 的 options 至少要有 2 个选项")
    if raw["answer"] not in options:
        raise QuestionBankError(
            f"{source.name}: 题目 {raw['id']} 的 answer={raw['answer']!r} 不在选项 {sorted(options)} 中"
        )

    difficulty = raw.get("difficulty", "easy")
    if difficulty not in VALID_DIFFICULTIES:
        raise QuestionBankError(
            f"{source.name}: 题目 {raw['id']} 的 difficulty 必须是 {sorted(VALID_DIFFICULTIES)} 之一"
        )

    distractors = raw.get("distractors") or {}
    unknown = set(distractors) - set(options)
    if unknown:
        raise QuestionBankError(f"{source.name}: 题目 {raw['id']} 的 distractors 含不存在的选项 {sorted(unknown)}")

    return Question(
        id=raw["id"],
        topic=raw["topic"],
        question=raw["question"],
        options=dict(options),
        answer=raw["answer"],
        explanation=raw["explanation"],
        difficulty=difficulty,
        distractors=dict(distractors),
        knowledge=list(raw.get("knowledge") or []),
        doc=raw.get("doc", ""),
        tags=list(raw.get("tags") or []),
    )


def _bank_signature() -> tuple[tuple[str, int, int], ...]:
    """题库文件的指纹：(文件名, mtime_ns, 大小)。任一文件变化都会得到不同的签名。"""
    if not QUESTIONS_DIR.exists():
        return ()
    return tuple(
        (path.name, stat.st_mtime_ns, stat.st_size)
        for path in sorted(QUESTIONS_DIR.glob("*.json"))
        for stat in (path.stat(),)
    )


_cache: dict[str, Any] = {"signature": None, "bank": None}


def load_questions() -> dict[str, Question]:
    """返回 {question_id: Question}。

    题库文件有增删改时（mtime / 大小 / 文件名变化）自动重新加载，
    不再需要手动调用 /api/questions/reload。解析失败时抛 QuestionBankError，
    不会用坏数据覆盖已经加载好的旧题库。
    """
    signature = _bank_signature()
    if _cache["bank"] is None or _cache["signature"] != signature:
        _cache["bank"] = _read_bank()
        _cache["signature"] = signature
    return _cache["bank"]


def _read_bank() -> dict[str, Question]:
    """读取并校验全部题目。"""
    if not QUESTIONS_DIR.exists():
        raise QuestionBankError(f"题库目录不存在: {QUESTIONS_DIR}")

    bank: dict[str, Question] = {}
    files = sorted(QUESTIONS_DIR.glob("*.json"))
    if not files:
        raise QuestionBankError(f"题库目录里没有任何 .json 文件: {QUESTIONS_DIR}")

    for path in files:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:  # pragma: no cover - 提示更友好
            raise QuestionBankError(f"{path.name}: JSON 解析失败 -> {exc}") from exc

        items = payload["questions"] if isinstance(payload, dict) else payload
        if not isinstance(items, list):
            raise QuestionBankError(f"{path.name}: 顶层必须是数组，或 {{\"questions\": [...]}}")

        for raw in items:
            question = _validate(raw, path)
            if question.id in bank:
                raise QuestionBankError(f"题目 id 重复: {question.id}")
            bank[question.id] = question

    return bank


def reload_questions() -> dict[str, Question]:
    """强制重新加载（保留给 /api/questions/reload，兼容原有用法）。"""
    _cache["bank"] = None
    return load_questions()


def topic_summary() -> list[dict[str, Any]]:
    bank = load_questions()
    counts: dict[str, int] = {}
    for question in bank.values():
        counts[question.topic] = counts.get(question.topic, 0) + 1
    return [
        {"topic": topic, "label": TOPIC_LABELS.get(topic, topic), "count": count}
        for topic, count in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    ]
