"""错题本导出的格式化逻辑：Markdown 结构、Anki CSV 的导入指令与 HTML 转义。

纯函数测试，不依赖数据库。输入结构与 service.list_wrong_questions 的返回值一致。
"""

from __future__ import annotations

import csv
import io
from datetime import datetime

from app.export import to_anki_csv, to_markdown


def _item(**overrides) -> dict:
    base = {
        "question_id": "basics-1",
        "topic": "basics",
        "topic_label": "基础语法与变量",
        "wrong_count": 2,
        "last_selected": "B",
        "first_wrong_at": "2024-01-01T10:00:00",
        "last_wrong_at": "2024-01-02T11:30:00",
        "mastered": False,
        "note": "",
        "question": {
            "id": "basics-1",
            "topic": "basics",
            "topic_label": "基础语法与变量",
            "difficulty": "easy",
            "question": "print(1 < 2) 的输出是？",
            "options": {"A": "False", "B": "True"},
        },
        "correct_answer": "B",
        "explanation": "1 < 2 为真。",
        "why_wrong": None,
        "knowledge": [],
        "doc": "",
    }
    base.update(overrides)
    return base


NOW = datetime(2024, 5, 1, 9, 15)


# --------------------------------------------------------------------------- #
# Markdown
# --------------------------------------------------------------------------- #
def test_markdown_empty_has_header_and_notice():
    text = to_markdown([], NOW)
    assert text.startswith("# KotoneGo 错题本")
    assert "题目数量：0" in text
    assert "没有错题" in text


def test_markdown_contains_question_options_and_answer():
    text = to_markdown([_item()], NOW)
    assert "## 1. print(1 < 2) 的输出是？" in text
    assert "- A. False" in text and "- B. True" in text
    assert "正确答案：**B**" in text
    assert "你最近选：**B**" in text
    assert "1 < 2 为真。" in text
    assert "导出时间：2024-05-01 09:15" in text


def test_markdown_status_and_wrong_count():
    text = to_markdown([_item(mastered=True, wrong_count=3)], NOW)
    assert "状态：已掌握，累计错 3 次" in text
    assert "待攻克" not in text


def test_markdown_optional_sections_only_when_present():
    bare = to_markdown([_item()], NOW)
    assert "为什么会错" not in bare
    assert "相关知识点" not in bare
    assert "我的笔记" not in bare

    full = to_markdown(
        [
            _item(
                why_wrong="误以为 < 是赋值",
                knowledge=["比较运算", "布尔值"],
                doc="04-operators",
                note="记住比较返回 bool",
            )
        ],
        NOW,
    )
    assert "**为什么会错**：误以为 < 是赋值" in full
    assert "**相关知识点**：比较运算、布尔值" in full
    assert "`04-operators`" in full
    assert "**我的笔记**：记住比较返回 bool" in full


def test_markdown_numbers_items_in_order():
    text = to_markdown([_item(question_id="a"), _item(question_id="b")], NOW)
    assert text.index("## 1.") < text.index("## 2.")
    assert "题目数量：2" in text


# --------------------------------------------------------------------------- #
# Anki CSV
# --------------------------------------------------------------------------- #
def _parse_csv(text: str) -> tuple[list[str], list[list[str]]]:
    lines = text.splitlines()
    directives = [line for line in lines if line.startswith("#")]
    body = "\n".join(line for line in lines if not line.startswith("#"))
    rows = list(csv.reader(io.StringIO(body)))
    return directives, rows


def test_anki_header_directives():
    directives, _ = _parse_csv(to_anki_csv([]))
    assert "#separator:comma" in directives
    assert "#html:true" in directives
    assert "#tags column:3" in directives


def test_anki_empty_has_no_rows():
    _, rows = _parse_csv(to_anki_csv([]))
    assert rows == []


def test_anki_row_has_front_back_and_tag():
    _, rows = _parse_csv(to_anki_csv([_item()]))
    assert len(rows) == 1
    front, back, tags = rows[0]
    assert "print(1 &lt; 2) 的输出是？" in front  # 题干中的 < 必须转义
    assert "A. False" in front and "B. True" in front
    assert "正确答案：B" in back
    assert "你选了 B" in back
    assert tags == "kotone_basics"


def test_anki_escapes_html_and_keeps_newlines_as_br():
    item = _item(explanation="第一行 <b>危险</b>\n第二行 & 结束")
    _, rows = _parse_csv(to_anki_csv([item]))
    back = rows[0][1]
    assert "&lt;b&gt;危险&lt;/b&gt;" in back
    assert "<br>第二行 &amp; 结束" in back
    assert "<b>危险</b>" not in back


def test_anki_commas_and_quotes_survive_csv_round_trip():
    item = _item(explanation='他说 "a,b" 很怪')
    _, rows = _parse_csv(to_anki_csv([item]))
    assert len(rows[0]) == 3  # 字段里的逗号不能拆坏列
    assert "&quot;a,b&quot;" in rows[0][1]  # 引号也被 HTML 转义，逐字段完整保留


def test_anki_tag_is_sanitized():
    _, rows = _parse_csv(to_anki_csv([_item(topic="weird topic/x")]))
    assert rows[0][2] == "kotone_weird_topic_x"
