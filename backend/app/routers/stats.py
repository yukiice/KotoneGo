"""错题本与统计接口。"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response

from .. import service
from ..export import to_anki_csv, to_markdown
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


@router.get(
    "/wrong-questions/export",
    summary="导出错题本（Markdown 或 Anki CSV）",
    response_class=Response,
)
def export_wrong_questions(
    topic: str | None = Query(default=None, description="只导出该主题，不传=全部"),
    format: Literal["markdown", "anki"] = Query(default="markdown", description="markdown=复习笔记，anki=可导入 Anki 的 CSV"),
    mastered: bool | None = Query(default=None, description="与列表接口一致：true/false/不传"),
) -> Response:
    items = service.list_wrong_questions(topic=topic, mastered=mastered)
    stamp = datetime.now().strftime("%Y%m%d")
    if format == "anki":
        body = to_anki_csv(items)
        media_type, filename = "text/csv; charset=utf-8", f"kotone-wrong-book-{stamp}.csv"
    else:
        body = to_markdown(items, datetime.now())
        media_type, filename = "text/markdown; charset=utf-8", f"kotone-wrong-book-{stamp}.md"
    return Response(
        content=body,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


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
