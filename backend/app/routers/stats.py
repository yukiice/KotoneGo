"""错题本与统计接口。"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from .. import service
from ..schemas import StatsResponse, UpdateWrongQuestionRequest, WrongQuestionItem

router = APIRouter(prefix="/api", tags=["wrong-book", "stats"])


def _handle(exc: Exception) -> HTTPException:
    if isinstance(exc, service.NotFoundError):
        return HTTPException(status_code=404, detail=str(exc))
    return HTTPException(status_code=400, detail=str(exc))


@router.get("/wrong-questions", response_model=list[WrongQuestionItem], summary="错题列表")
def list_wrong_questions(
    topic: str | None = Query(default=None),
    mastered: bool | None = Query(default=None, description="true=已掌握，false=待攻克，不传=全部"),
) -> list[dict]:
    return service.list_wrong_questions(topic=topic, mastered=mastered)


@router.patch("/wrong-questions/{question_id}", response_model=WrongQuestionItem, summary="标记掌握 / 写笔记")
def update_wrong_question(question_id: str, payload: UpdateWrongQuestionRequest) -> dict:
    try:
        return service.update_wrong_question(
            question_id, mastered=payload.mastered, note=payload.note
        )
    except service.NotFoundError as exc:
        raise _handle(exc) from exc


@router.delete("/wrong-questions/{question_id}", status_code=204, summary="从错题本移除")
def delete_wrong_question(question_id: str) -> None:
    try:
        service.delete_wrong_question(question_id)
    except service.NotFoundError as exc:
        raise _handle(exc) from exc


@router.get("/stats", response_model=StatsResponse, summary="学习统计")
def get_stats() -> dict:
    return service.get_stats()
