#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import re
from collections import OrderedDict
from pathlib import Path

from pypdf import PdfReader


STAGES = ["初中基础", "高一上", "高一下", "高二", "高三"]
ROW_RE = re.compile(r"^(\d+)\s+([1-4])\*([1-6])\s+(.+?)\s+®")
POS_RE = re.compile(
    r"\s(?:n|vt|vi|v|adj|adv|abbr|prep|conj|pron|num|art|modal|a|ad)"
    r"(?:[.&,/]|(?=[\u3400-\u9fff]))",
    re.I,
)
SINGLE_RE = re.compile(r"^[A-Za-z][A-Za-z'.-]*$")
COMMON_CAPITALISATION_FIXES = {"Confused": "confused", "Lower": "lower"}


def norm(value: str) -> str:
    value = value.casefold().replace("’", "'")
    return re.sub(r"[^a-z0-9'-]+", "", value)


def compact_zh(entry: dict) -> str:
    return "；".join(
        f"{sense.get('pos', '')} {sense.get('zh', '')}".strip()
        for sense in entry.get("senses", [])[:3]
    )


def section_for(number: int, book_number: int) -> tuple[str, str]:
    if number < 1200:
        books = {1: "必修第一册", 2: "必修第二册", 3: "必修第三册"}
        stages = {1: "高一上", 2: "高一下", 3: "高一下"}
    else:
        books = {1: "选择性必修第一册", 2: "选择性必修第二册", 3: "选择性必修第三册", 4: "选择性必修第四册"}
        stages = {1: "高二", 2: "高二", 3: "高三", 4: "高三"}
    return books[book_number], stages[book_number]


def parse_pdf(path: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for page_number, page in enumerate(PdfReader(str(path)).pages, 1):
        for raw_line in (page.extract_text() or "").splitlines():
            match = ROW_RE.match(raw_line.strip())
            if not match:
                continue
            number, book_number, unit, body = match.groups()
            number_i = int(number)
            body = body.strip()
            ipa_match = re.search(r"\s+(/[^/]+/)\s*$", body)
            ipa = ipa_match.group(1) if ipa_match else ""
            if ipa_match:
                body = body[: ipa_match.start()].strip()
            pos_match = POS_RE.search(body)
            chinese_match = re.search(r"[\u3400-\u9fff]", body)
            cut_points = [
                value
                for value in (
                    pos_match.start() if pos_match else None,
                    chinese_match.start() if chinese_match else None,
                )
                if value is not None
            ]
            cut = min(cut_points) if cut_points else len(body)
            word = body[:cut].strip().rstrip("([（,，")
            word = COMMON_CAPITALISATION_FIXES.get(word, word)
            gloss = body[cut:].strip()
            book, stage = section_for(number_i, int(book_number))
            rows.append(
                {
                    "number": str(number_i),
                    "code": f"{book_number}*{unit}",
                    "word": word,
                    "gloss": gloss,
                    "ipa": ipa,
                    "book": book,
                    "stage": stage,
                    "page": str(page_number),
                    "is_single_word": str(bool(SINGLE_RE.fullmatch(word))),
                    "is_likely_proper_name": str(
                        bool(word[:1].isupper() and not word.isupper() and word not in COMMON_CAPITALISATION_FIXES.values())
                    ),
                }
            )
    numbers = [int(row["number"]) for row in rows]
    if numbers != list(range(1, 2597)):
        raise ValueError("PDF entry numbering is incomplete or out of order")
    return rows


def append_unique(value: str, additions: str) -> str:
    items = [item for item in value.split("；") if item]
    for item in additions.split("；"):
        if item and item not in items:
            items.append(item)
    return "；".join(items)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf", required=True, type=Path)
    parser.add_argument("--baseline-csv", required=True, type=Path)
    parser.add_argument("--junior-data", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    pdf_rows = parse_pdf(args.pdf)
    pdf_singles = [row for row in pdf_rows if row["is_single_word"] == "True"]
    pdf_phrases = [row for row in pdf_rows if row["is_single_word"] != "True"]
    baseline = list(csv.DictReader(args.baseline_csv.open(encoding="utf-8-sig")))
    baseline_main = [row for row in baseline if row["proper_noun_marked"].lower() != "true"]
    junior = json.loads(args.junior_data.read_text(encoding="utf-8"))
    pdf_single_keys = {norm(row["word"]) for row in pdf_singles}
    baseline_keys = {norm(row["word"]) for row in baseline_main}

    merged: OrderedDict[str, dict[str, str]] = OrderedDict()
    for entry in junior:
        key = norm(entry["w"])
        merged[key] = {
            "word": entry["w"],
            "stages": "初中基础",
            "books": "初中专属词光",
            "edition": "初中累计基础词",
            "official_match": "False",
            "needs_review": "False",
            "proper_noun_marked": "False",
            "textbook_zh_gloss": compact_zh(entry),
            "source_pages": "初中专属词光词库",
            "ipa": entry.get("uk") or entry.get("us") or "",
            "source_type": "junior_cumulative",
        }

    for row in baseline_main:
        key = norm(row["word"])
        if key in merged:
            target = merged[key]
            target["stages"] = append_unique(target["stages"], row["stages"])
            target["books"] = append_unique(target["books"], row["books"])
            target["source_pages"] = append_unique(target["source_pages"], row["source_pages"])
            target["source_type"] = append_unique(target["source_type"], "textbook_appendix")
        else:
            merged[key] = {**row, "ipa": "", "source_type": "textbook_appendix"}

    new_from_pdf = 0
    for row in pdf_singles:
        key = norm(row["word"])
        if key in merged:
            target = merged[key]
            target["stages"] = append_unique(target["stages"], row["stage"])
            target["books"] = append_unique(target["books"], row["book"])
            target["source_pages"] = append_unique(target["source_pages"], f"用户提供PDF@第{row['page']}页")
            target["source_type"] = append_unique(target["source_type"], "supplied_pdf")
            if not target.get("ipa"):
                target["ipa"] = row["ipa"]
        else:
            new_from_pdf += 1
            merged[key] = {
                "word": row["word"],
                "stages": row["stage"],
                "books": row["book"],
                "edition": "用户提供的高中新人教版单词表",
                "official_match": "False",
                "needs_review": "False",
                "proper_noun_marked": "False",
                "textbook_zh_gloss": row["gloss"] or "教材词汇",
                "source_pages": f"用户提供PDF@第{row['page']}页",
                "ipa": row["ipa"],
                "source_type": "supplied_pdf",
            }

    merged_rows = list(merged.values())
    merged_rows.sort(key=lambda row: (STAGES.index(row["stages"].split("；")[0]), row["word"].casefold()))

    pdf_fields = list(pdf_rows[0])
    for name, records in [
        ("用户提供词表_逐条解析.csv", pdf_rows),
        ("用户提供词表_独立词.csv", pdf_singles),
        ("用户提供词表_短语与专名词组.csv", pdf_phrases),
    ]:
        with (args.output_dir / name).open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=pdf_fields)
            writer.writeheader()
            writer.writerows(records)

    merged_fields = list(merged_rows[0])
    with (args.output_dir / "高中累计词库_合并源.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=merged_fields)
        writer.writeheader()
        writer.writerows(merged_rows)

    stage_counts = {stage: sum(row["stages"].split("；")[0] == stage for row in merged_rows) for stage in STAGES}
    summary = {
        "pdf_total_entries": len(pdf_rows),
        "pdf_single_word_entries": len(pdf_singles),
        "pdf_unique_single_words": len(pdf_single_keys),
        "pdf_phrase_or_multiword_entries": len(pdf_phrases),
        "baseline_high_school_main_words": len(baseline_main),
        "pdf_overlap_with_baseline": len(pdf_single_keys & baseline_keys),
        "pdf_new_vs_baseline": len(pdf_single_keys - baseline_keys),
        "baseline_not_in_pdf": len(baseline_keys - pdf_single_keys),
        "junior_cumulative_words": len(junior),
        "new_single_words_from_pdf": new_from_pdf,
        "cumulative_unique_words": len(merged_rows),
        "stage_counts_by_first_appearance": stage_counts,
    }
    (args.output_dir / "用户提供词表_比对摘要.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
