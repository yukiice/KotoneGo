"""错题本导出：把 list_wrong_questions 的结果转成 Markdown 或 Anki 可导入的 CSV。

只做格式化，不访问数据库，便于单元测试。输入是 service.list_wrong_questions 的返回值。
"""

from __future__ import annotations

import csv
import html
import io
import re
from datetime import datetime
from typing import Any

_TAG_UNSAFE = re.compile(r"[^0-9A-Za-z_\-]+")


def _mark_status(item: dict[str, Any]) -> str:
    return "已掌握" if item["mastered"] else "待攻克"


def to_markdown(items: list[dict[str, Any]], generated_at: datetime) -> str:
    """生成 Markdown 错题本，每题一节，适合打印或放进笔记软件。"""
    lines: list[str] = [
        "# KotoneGo 错题本",
        "",
        f"- 导出时间：{generated_at.strftime('%Y-%m-%d %H:%M')}",
        f"- 题目数量：{len(items)}",
        "",
    ]
    if not items:
        lines += ["当前筛选条件下没有错题。", ""]
        return "\n".join(lines)

    for index, item in enumerate(items, start=1):
        question = item["question"]
        selected = item["last_selected"] or "—"
        lines += [
            f"## {index}. {question['question'].strip()}",
            "",
            f"- 主题：{item['topic_label']}",
            f"- 状态：{_mark_status(item)}，累计错 {item['wrong_count']} 次",
            f"- 最近错误：{item['last_wrong_at'] or '—'}",
            "",
        ]
        for key, text in question["options"].items():
            lines.append(f"- {key}. {text}")
        lines += [
            "",
            f"你最近选：**{selected}**　正确答案：**{item['correct_answer']}**",
            "",
            "**解析**：" + item["explanation"].strip(),
        ]
        if item.get("why_wrong"):
            lines += ["", "**为什么会错**：" + item["why_wrong"].strip()]
        if item.get("knowledge"):
            lines += ["", "**相关知识点**：" + "、".join(item["knowledge"])]
        if item.get("doc"):
            lines += ["", f"**对应文档**：`{item['doc']}`"]
        if item.get("note"):
            lines += ["", "**我的笔记**：" + item["note"].strip()]
        lines.append("")

    return "\n".join(lines)


def _html_block(text: str) -> str:
    """Anki 的 html 字段：先转义，再把换行变成 <br>，避免题干里的 < > 被当成标签。"""
    return "<br>".join(html.escape(line) for line in text.strip().splitlines())


def _anki_front(item: dict[str, Any]) -> str:
    question = item["question"]
    parts = [f"<b>{_html_block(question['question'])}</b>"]
    options = [f"{html.escape(key)}. {html.escape(text)}" for key, text in question["options"].items()]
    parts.append("<br>".join(options))
    return "<br><br>".join(parts)


def _anki_back(item: dict[str, Any]) -> str:
    parts = [f"<b>正确答案：{html.escape(item['correct_answer'])}</b>（你选了 {html.escape(item['last_selected'] or '—')}）"]
    parts.append("<b>解析</b><br>" + _html_block(item["explanation"]))
    if item.get("why_wrong"):
        parts.append("<b>为什么会错</b><br>" + _html_block(item["why_wrong"]))
    if item.get("knowledge"):
        parts.append("<b>知识点</b>：" + html.escape("、".join(item["knowledge"])))
    if item.get("note"):
        parts.append("<b>我的笔记</b><br>" + _html_block(item["note"]))
    return "<br><br>".join(parts)


def _anki_tag(topic: str) -> str:
    """Anki 标签不能含空格；主题 ID 本身是 ASCII，这里再做一次兜底清洗。"""
    return "kotone_" + (_TAG_UNSAFE.sub("_", topic) or "misc")


def to_anki_csv(items: list[dict[str, Any]]) -> str:
    """生成 Anki 可直接导入的 CSV（逗号分隔，字段为 HTML）。

    文件头部的 `#` 行是 Anki 的导入指令：指定分隔符、允许 HTML、第 3 列为标签。
    导入时请选择 Basic（或任何含 Front/Back 两个字段的笔记类型）。
    """
    buffer = io.StringIO()
    buffer.write("#separator:comma\n#html:true\n#tags column:3\n")
    writer = csv.writer(buffer, quoting=csv.QUOTE_MINIMAL, lineterminator="\n")
    for item in items:
        writer.writerow([_anki_front(item), _anki_back(item), _anki_tag(item["topic"])])
    return buffer.getvalue()
