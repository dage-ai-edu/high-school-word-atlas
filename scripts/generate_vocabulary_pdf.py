#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/high-school-source/高中累计词库_合并源.csv"
ATLAS_DATA = ROOT / "data/word-atlas.json"
OUTPUT = ROOT / "data/high-school-source/高中英语累计词汇汇总_新人教版.pdf"
FONT = "/System/Library/Fonts/Supplemental/Arial Unicode.ttf"
STAGES = ["初中基础", "高一上", "高一下", "高二", "高三"]
RESOURCE_BY_WORD: dict[str, str] = {}


def first_stage(row: dict[str, str]) -> str:
    return row["stages"].split("；")[0]


def page_decor(canvas, doc) -> None:
    canvas.saveState()
    canvas.setFont("CJK", 8)
    canvas.setFillColor(colors.HexColor("#6D7482"))
    canvas.drawString(16 * mm, 9 * mm, "高中英语累计词汇汇总｜新人教版")
    canvas.drawRightString(281 * mm, 9 * mm, f"第 {doc.page} 页")
    canvas.restoreState()


def word_table(rows: list[dict[str, str]], include_stage: bool = False) -> Table:
    header = ["单词", "教材释义", "来源册次", "词光资源"]
    if include_stage:
        header.insert(0, "首次阶段")
    body = [header]
    for row in rows:
        data = [
            Paragraph(row["word"], STYLES["word"]),
            Paragraph(row["textbook_zh_gloss"] or "—", STYLES["cell"]),
            Paragraph(row["books"], STYLES["cell"]),
            RESOURCE_BY_WORD.get(row["word"].casefold(), "教材补充"),
        ]
        if include_stage:
            data.insert(0, first_stage(row))
        body.append(data)
    widths = [28 * mm, 92 * mm, 70 * mm, 27 * mm]
    if include_stage:
        widths = [22 * mm, 28 * mm, 82 * mm, 65 * mm, 27 * mm]
    table = Table(body, colWidths=widths, repeatRows=1, hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#172238")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, -1), "CJK"),
                ("FONTSIZE", (0, 0), (-1, 0), 8.5),
                ("FONTSIZE", (0, 1), (-1, -1), 8),
                ("LEADING", (0, 1), (-1, -1), 11),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#CBD2DD")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F5F7FA")]),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return table


pdfmetrics.registerFont(TTFont("CJK", FONT))
base = getSampleStyleSheet()
STYLES = {
    "title": ParagraphStyle("TitleCJK", parent=base["Title"], fontName="CJK", fontSize=28, leading=36, textColor=colors.HexColor("#172238"), alignment=TA_CENTER),
    "subtitle": ParagraphStyle("SubtitleCJK", parent=base["Normal"], fontName="CJK", fontSize=12, leading=20, textColor=colors.HexColor("#586174"), alignment=TA_CENTER),
    "h1": ParagraphStyle("H1CJK", parent=base["Heading1"], fontName="CJK", fontSize=19, leading=25, textColor=colors.HexColor("#172238"), spaceAfter=8),
    "body": ParagraphStyle("BodyCJK", parent=base["BodyText"], fontName="CJK", fontSize=10, leading=17, textColor=colors.HexColor("#323A49")),
    "cell": ParagraphStyle("CellCJK", parent=base["BodyText"], fontName="CJK", fontSize=8, leading=11),
    "word": ParagraphStyle("Word", parent=base["BodyText"], fontName="CJK", fontSize=8.5, leading=11, textColor=colors.HexColor("#18243B")),
}


def main() -> None:
    with SOURCE.open(encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    main_words = rows
    counts = Counter(first_stage(row) for row in main_words)
    atlas_entries = json.loads(ATLAS_DATA.read_text(encoding="utf-8"))
    for entry in atlas_entries:
        if entry["id"].startswith("high-"):
            resource = "教材补充"
        elif entry["id"].startswith("primary-"):
            resource = "初中补充"
        else:
            resource = "官方完整"
        RESOURCE_BY_WORD[entry["w"].casefold()] = resource
    resource_counts = Counter(RESOURCE_BY_WORD.values())

    doc = SimpleDocTemplate(
        str(OUTPUT),
        pagesize=landscape(A4),
        rightMargin=14 * mm,
        leftMargin=14 * mm,
        topMargin=14 * mm,
        bottomMargin=16 * mm,
        title="高中英语累计词汇汇总（新人教版）",
        author="达哥 AI 自学",
    )
    story = [
        Spacer(1, 35 * mm),
        Paragraph("高中英语累计词汇汇总", STYLES["title"]),
        Spacer(1, 5 * mm),
        Paragraph("初中基础 + 人教版高中必修 3 册 + 选择性必修 4 册", STYLES["subtitle"]),
        Spacer(1, 16 * mm),
        Paragraph(
            f"累计学习词共 {len(main_words):,} 个：初中基础 {counts['初中基础']}、高一上 {counts['高一上']}、高一下 {counts['高一下']}、高二 {counts['高二']}、高三 {counts['高三']}。<br/>"
            f"其中 {resource_counts['官方完整']:,} 个匹配词光官方词库，{resource_counts['初中补充']} 个复用初中补充词条，{resource_counts['教材补充']} 个为高中教材补充词。",
            STYLES["subtitle"],
        ),
        Spacer(1, 14 * mm),
        Paragraph("说明：用户提供 PDF 中的 449 条短语或多词项目已单独保存为 CSV，不混入单词学习库；同一单词跨学段出现时只保留一条，并标注全部来源。", STYLES["subtitle"]),
        PageBreak(),
    ]

    for stage_index, stage in enumerate(STAGES):
        stage_rows = [row for row in main_words if first_stage(row) == stage]
        stage_rows.sort(key=lambda row: row["word"].casefold())
        matched = sum(RESOURCE_BY_WORD.get(row["word"].casefold()) == "官方完整" for row in stage_rows)
        story.extend(
            [
                Paragraph(f"{stage}｜{len(stage_rows)} 词", STYLES["h1"]),
                Paragraph(f"官方词光匹配 {matched} 个，非官方补充 {len(stage_rows)-matched} 个。", STYLES["body"]),
                Spacer(1, 3 * mm),
                word_table(stage_rows),
            ]
        )
        if stage_index < len(STAGES) - 1:
            story.append(PageBreak())

    doc.build(story, onFirstPage=page_decor, onLaterPages=page_decor)
    print(OUTPUT)


if __name__ == "__main__":
    main()
