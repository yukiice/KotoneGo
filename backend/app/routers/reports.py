"""题目纠错上报接口。

学习者在答题页 / 错题本里点「这题有问题」即可提交；本地应用没有登录，
查看列表的接口同样对本机开放，适合个人或小规模使用。
"""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, HTTPException, Query

from .. import service
from ..schemas import QuestionReportItem, ReportQuestionRequest, UpdateReportStatusRequest

router = APIRouter(prefix="/api", tags=["question-reports"])


@router.post(
    "/questions/{question_id}/reports",
    response_model=QuestionReportItem,
    status_code=201,
    summary="报告题目有问题（答案有误 / 解析不准确 / 表述不清 / 其他）",
)
def report_question(question_id: str, payload: ReportQuestionRequest) -> dict:
    try:
        return service.create_report(question_id, payload.category, payload.message)
    except service.NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except service.ConflictError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/question-reports", response_model=list[QuestionReportItem], summary="查看纠错上报列表")
def list_question_reports(
    status: Literal["open", "resolved"] | None = Query(default=None, description="不传=全部"),
) -> list[dict]:
    return service.list_reports(status=status)


@router.patch(
    "/question-reports/{report_id}",
    response_model=QuestionReportItem,
    summary="标记上报已修复 / 重新打开",
)
def update_question_report(report_id: int, payload: UpdateReportStatusRequest) -> dict:
    try:
        return service.update_report_status(report_id, payload.status)
    except service.NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
