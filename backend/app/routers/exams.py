"""考试相关接口。"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from .. import service
from ..schemas import (
    AnswerFeedback,
    CreateExamRequest,
    ExamDetail,
    ExamHistoryItem,
    ExamPublic,
    ExamResult,
    SubmitAnswerRequest,
)

router = APIRouter(prefix="/api/exams", tags=["exams"])


def _handle(exc: Exception) -> HTTPException:
    if isinstance(exc, service.NotFoundError):
        return HTTPException(status_code=404, detail=str(exc))
    return HTTPException(status_code=400, detail=str(exc))


@router.post("", response_model=ExamPublic, summary="开始一场考试（随机抽题）")
def create_exam(payload: CreateExamRequest) -> dict:
    try:
        return service.create_exam(
            size=payload.size,
            topics=payload.topics,
            difficulty=payload.difficulty,
            only_wrong=payload.only_wrong,
        )
    except (service.NotFoundError, service.ConflictError) as exc:
        raise _handle(exc) from exc


@router.get("", response_model=list[ExamHistoryItem], summary="考试历史")
def list_exams(limit: int = Query(default=50, ge=1, le=200), offset: int = Query(default=0, ge=0)) -> list[dict]:
    return service.list_exams(limit=limit, offset=offset)


@router.get("/{exam_id}", response_model=ExamDetail, summary="考试详情（含每题对错与解析）")
def get_exam(exam_id: str) -> dict:
    try:
        return service.get_exam_detail(exam_id)
    except service.NotFoundError as exc:
        raise _handle(exc) from exc


@router.post("/{exam_id}/answers", response_model=AnswerFeedback, summary="提交单题答案，立即返回对错与理由")
def submit_answer(exam_id: str, payload: SubmitAnswerRequest) -> dict:
    try:
        return service.submit_answer(exam_id, payload.question_id, payload.selected)
    except (service.NotFoundError, service.ConflictError) as exc:
        raise _handle(exc) from exc


@router.post("/{exam_id}/finish", response_model=ExamResult, summary="交卷")
def finish_exam(exam_id: str) -> dict:
    try:
        return service.finish_exam(exam_id)
    except service.NotFoundError as exc:
        raise _handle(exc) from exc


@router.delete("/{exam_id}", status_code=204, summary="删除一场考试记录")
def delete_exam(exam_id: str) -> None:
    try:
        service.delete_exam(exam_id)
    except service.NotFoundError as exc:
        raise _handle(exc) from exc
