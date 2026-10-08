"""请求 / 响应模型（Pydantic v2）。"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class CreateExamRequest(BaseModel):
    size: int = Field(default=10, ge=1, le=60, description="本场考试题量")
    topics: list[str] = Field(default_factory=list, description="留空表示全部主题")
    difficulty: Literal["easy", "medium", "hard", "any"] = "any"
    only_wrong: bool = Field(default=False, description="只从错题本里抽题")


class SubmitAnswerRequest(BaseModel):
    question_id: str
    selected: str = Field(min_length=1, max_length=8)


class ExamQuestionPublic(BaseModel):
    id: str
    topic: str
    topic_label: str
    difficulty: str
    question: str
    options: dict[str, str]
    selected: str | None = None
    is_correct: bool | None = None


class ExamPublic(BaseModel):
    id: str
    created_at: str
    status: str
    size: int
    topics: list[str]
    points_per_question: int
    questions: list[ExamQuestionPublic]
    answered_count: int = 0
    correct_count: int = 0
    score: int = 0


class AnswerFeedback(BaseModel):
    question_id: str
    selected: str
    is_correct: bool
    correct_answer: str
    explanation: str
    why_wrong: str | None = None
    knowledge: list[str] = Field(default_factory=list)
    doc: str = ""
    topic: str
    topic_label: str
    question: str
    options: dict[str, str]
    answered_count: int
    total: int
    correct_count: int
    score: int


class ExamResult(BaseModel):
    id: str
    created_at: str
    finished_at: str | None
    status: str
    size: int
    score: int
    correct_count: int
    wrong_count: int
    duration_seconds: int
    by_topic: list[dict[str, Any]] = Field(default_factory=list)


class ExamHistoryItem(BaseModel):
    id: str
    created_at: str
    finished_at: str | None
    status: str
    size: int
    score: int
    correct_count: int
    duration_seconds: int
    topics: list[str] = Field(default_factory=list)


class AnswerDetail(BaseModel):
    question: ExamQuestionPublic
    selected: str | None
    is_correct: bool | None
    correct_answer: str
    explanation: str
    why_wrong: str | None = None
    knowledge: list[str] = Field(default_factory=list)
    doc: str = ""


class ExamDetail(BaseModel):
    exam: ExamResult
    answers: list[AnswerDetail]


class WrongQuestionItem(BaseModel):
    question_id: str
    topic: str
    topic_label: str
    wrong_count: int
    last_selected: str | None
    first_wrong_at: str
    last_wrong_at: str
    mastered: bool
    note: str
    question: ExamQuestionPublic
    correct_answer: str
    explanation: str
    why_wrong: str | None = None
    knowledge: list[str] = Field(default_factory=list)
    doc: str = ""


class UpdateWrongQuestionRequest(BaseModel):
    mastered: bool | None = None
    note: str | None = Field(default=None, max_length=2000)


class TopicStat(BaseModel):
    topic: str
    label: str
    attempts: int
    correct: int
    accuracy: float
    bank_count: int
    wrong_open: int


class StatsResponse(BaseModel):
    exam_count: int
    finished_exam_count: int
    answered_questions: int
    avg_score: float
    best_score: int
    total_minutes: float
    bank_size: int
    wrong_open_count: int
    wrong_mastered_count: int
    by_topic: list[TopicStat]
    recent_exams: list[ExamHistoryItem]
