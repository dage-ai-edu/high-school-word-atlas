#!/usr/bin/env python3
"""Extract textbook vocabulary and build the junior-only Word Atlas dataset."""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import shutil
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[1]
LIBRARY = Path(os.environ.get("JUNIOR_TEXTBOOK_LIBRARY", ROOT / "textbooks"))
WORK = ROOT / "work/textbook-vocabulary"
OCR_TEXT = WORK / "scanned-pages-ocr.txt"
PUBLIC = ROOT / "public/atlas"
DATA = ROOT / "data"
AUDIT_DIR = DATA / "junior-source"
AUDIT_CSV = AUDIT_DIR / "word-match-audit.csv"
UNMATCHED_CSV = AUDIT_DIR / "unmatched-candidates.csv"
SUMMARY_JSON = AUDIT_DIR / "match-summary.json"
TARGET_JSON = AUDIT_DIR / "junior-word-ids.json"


@dataclass(frozen=True)
class Source:
    key: str
    label: str
    grade: int
    term: int
    path: Path
    first_page: int
    last_page: int
    method: str


SOURCES = [
    Source("g7a", "七年级上册", 7, 1, LIBRARY / "01_七年级/03_英语/01_上册/01英语七年级上册电子课本.pdf", 115, 121, "text"),
    Source("g7b", "七年级下册", 7, 2, LIBRARY / "01_七年级/03_英语/02_下册/英语七年级下册电子课本.pdf", 106, 114, "text"),
    Source("g8a", "八年级上册", 8, 1, LIBRARY / "02_八年级/03_英语/01_上册/01英语八年级上册电子课本.pdf", 120, 131, "text"),
    Source("g8b", "八年级下册", 8, 2, LIBRARY / "02_八年级/03_英语/02_下册/英语八年级下册电子课本.pdf", 122, 134, "ocr"),
    Source("g9a", "九年级上册", 9, 1, LIBRARY / "03_九年级/03_英语/01_上册/26秋人教英语课本九年级上册彩版.pdf", 115, 124, "ocr"),
]


SKIP = {
    "vocabulary in each unit",
    "vocabulary",
    "unit",
    "starter unit",
    "adj",
    "adv",
    "n",
    "v",
    "pron",
    "prep",
    "conj",
    "interj",
    "modal v",
}
HEADWORD_BEFORE_IPA = re.compile(
    r"([A-Za-z][A-Za-z'’.-]*(?:\s+[A-Za-z][A-Za-z'’.-]*){0,4})\s*/"
)
PHRASE_BEFORE_CHINESE = re.compile(
    r"^\s*([A-Za-z][A-Za-z'’.-]*(?:\s+[A-Za-z][A-Za-z'’.-]*){0,5})\s+(?=[\u3400-\u9fff])"
)


def normalize(value: str) -> str:
    value = value.lower().replace("’", "'").replace("“", "").replace("”", "")
    value = re.sub(r"[^a-z0-9' -]+", " ", value)
    return re.sub(r"\s+", " ", value).strip(" .-'_")


def suffix_match(raw: str, atlas_words: dict[str, str]) -> str | None:
    cleaned = normalize(raw)
    if not cleaned:
        return None
    tokens = cleaned.split()
    for count in range(min(5, len(tokens)), 0, -1):
        candidate = " ".join(tokens[-count:])
        if candidate in atlas_words and candidate not in SKIP:
            return candidate
    return None


def ocr_pages() -> dict[tuple[str, int], str]:
    if not OCR_TEXT.is_file():
        raise FileNotFoundError(OCR_TEXT)
    result: dict[tuple[str, int], list[str]] = defaultdict(list)
    key: tuple[str, int] | None = None
    marker = re.compile(r"=== .*?/(eight-down|nine-up)-(\d+)\.png ===")
    for line in OCR_TEXT.read_text(encoding="utf-8").splitlines():
        match = marker.match(line)
        if match:
            source_key = "g8b" if match.group(1) == "eight-down" else "g9a"
            key = (source_key, int(match.group(2)))
            continue
        if key:
            result[key].append(line)
    return {key: "\n".join(lines) for key, lines in result.items()}


def page_texts() -> list[tuple[Source, int, str]]:
    scanned = ocr_pages()
    pages = []
    for source in SOURCES:
        if not source.path.is_file():
            raise FileNotFoundError(source.path)
        if source.method == "text":
            reader = PdfReader(source.path)
            for page_number in range(source.first_page, source.last_page + 1):
                pages.append((source, page_number, reader.pages[page_number - 1].extract_text() or ""))
        else:
            for page_number in range(source.first_page, source.last_page + 1):
                key = (source.key, page_number)
                if key not in scanned:
                    raise KeyError(f"Missing OCR page: {key}")
                pages.append((source, page_number, scanned[key]))
    return pages


def extract(atlas_words: dict[str, str], atlas_original: dict[str, str]) -> tuple[list[dict], list[dict]]:
    matched: list[dict] = []
    unmatched: list[dict] = []
    seen_page_ids: set[tuple[str, int, str]] = set()
    for source, page_number, text in page_texts():
        for line_number, line in enumerate(text.splitlines(), 1):
            stripped = line.strip()
            if not stripped or "Vocabulary in Each Unit" in stripped:
                continue
            candidates: list[tuple[str, str]] = []
            if source.method == "text" and "/" in stripped:
                candidates.append((stripped.split("/", 1)[0], "ipa"))
            elif source.method == "ocr" and "/" in stripped:
                parts = stripped.split("/")
                for prefix_text in parts[0::2]:
                    raw_match = re.search(r"([A-Za-z][A-Za-z'’.-]*(?:\s+[A-Za-z][A-Za-z'’.-]*){0,4})\s*$", prefix_text)
                    if not raw_match:
                        continue
                    raw = raw_match.group(1)
                    before = prefix_text[max(0, raw_match.start(1) - 8) : raw_match.start(1)]
                    if "(" in before or re.search(r"\b(?:adj|adv|pron|prep|conj|interj|modal|pl|v|n)\.\s*$", before, re.I):
                        continue
                    candidates.append((raw, "ipa"))
            phrase = PHRASE_BEFORE_CHINESE.match(stripped)
            if phrase and "/" not in stripped[: phrase.end()]:
                candidates.append((phrase.group(1), "phrase"))

            for raw, evidence in candidates:
                normalized_raw = normalize(raw)
                normalized = (
                    suffix_match(raw, atlas_words)
                    if evidence == "ipa" and source.method == "ocr"
                    else normalized_raw if normalized_raw in atlas_words else None
                )
                if normalized:
                    atlas_id = atlas_words[normalized]
                    raw_headword = raw.strip().split()[-1] if raw.strip() else ""
                    official_word = atlas_original[atlas_id]
                    if raw_headword.startswith("-"):
                        continue
                    if raw_headword[:1].isupper() and official_word[:1].islower():
                        continue
                    page_key = (source.key, page_number, atlas_id)
                    if page_key in seen_page_ids:
                        continue
                    seen_page_ids.add(page_key)
                    matched.append(
                        {
                            "id": atlas_id,
                            "word": normalized,
                            "source_key": source.key,
                            "source": source.label,
                            "grade": source.grade,
                            "term": source.term,
                            "pdf_page": page_number,
                            "line": line_number,
                            "match": "direct",
                            "raw": raw,
                        }
                    )
                elif evidence == "ipa":
                    raw_tokens = raw.split()
                    if not raw_tokens:
                        continue
                    candidate = normalize(raw_tokens[-1])
                    if len(candidate) >= 2 and candidate not in SKIP:
                        unmatched.append(
                            {
                                "candidate": candidate,
                                "source": source.label,
                                "pdf_page": page_number,
                                "line": line_number,
                                "raw": raw,
                            }
                        )
    return matched, unmatched


def write_audit(matched: list[dict], unmatched: list[dict], atlas_entries: dict[str, dict]) -> list[str]:
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    first_seen: dict[str, dict] = {}
    sources_by_id: dict[str, list[str]] = defaultdict(list)
    for row in matched:
        first_seen.setdefault(row["id"], row)
        source_ref = f'{row["source"]} PDF第{row["pdf_page"]}页'
        if source_ref not in sources_by_id[row["id"]]:
            sources_by_id[row["id"]].append(source_ref)
    ordered = sorted(first_seen, key=lambda word_id: (
        first_seen[word_id]["grade"], first_seen[word_id]["term"], first_seen[word_id]["pdf_page"], first_seen[word_id]["line"]
    ))

    with AUDIT_CSV.open("w", encoding="utf-8-sig", newline="") as handle:
        fields = ["order", "id", "word", "cefr", "topic", "first_source", "first_pdf_page", "all_sources", "match", "raw"]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for order, word_id in enumerate(ordered, 1):
            row = first_seen[word_id]
            entry = atlas_entries[word_id]
            writer.writerow(
                {
                    "order": order,
                    "id": word_id,
                    "word": entry["w"],
                    "cefr": entry["cefr"],
                    "topic": entry["topic"],
                    "first_source": row["source"],
                    "first_pdf_page": row["pdf_page"],
                    "all_sources": "；".join(sources_by_id[word_id]),
                    "match": row["match"],
                    "raw": row["raw"],
                }
            )
    unique_unmatched = {(row["candidate"], row["source"], row["pdf_page"]): row for row in unmatched}
    with UNMATCHED_CSV.open("w", encoding="utf-8-sig", newline="") as handle:
        fields = ["candidate", "source", "pdf_page", "line", "raw"]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(sorted(unique_unmatched.values(), key=lambda row: (row["source"], row["pdf_page"], row["line"])))

    summary = {
        "official_source_words": 7298,
        "available_dataset_words": len(atlas_entries),
        "matched_unique_words": len(ordered),
        "direct_occurrences": sum(row["match"] == "direct" for row in matched),
        "fuzzy_occurrences": sum(row["match"] == "fuzzy" for row in matched),
        "unmatched_candidates": len(unique_unmatched),
        "by_source": {
            source.label: len({row["id"] for row in matched if row["source_key"] == source.key})
            for source in SOURCES
        },
    }
    SUMMARY_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    TARGET_JSON.write_text(json.dumps(ordered, ensure_ascii=False, indent=2), encoding="utf-8")
    return ordered


def build_dataset(ordered: list[str], atlas_entries: dict[str, dict], prune_media: bool) -> None:
    old_index = json.loads((PUBLIC / "index.json").read_text(encoding="utf-8"))
    old_rows = {row[0]: row for row in old_index["words"]}
    entries = []
    rows = []
    for word_id in ordered:
        entry = dict(atlas_entries[word_id])
        media = old_rows[word_id][6]
        entry["m"] = media
        entries.append(entry)
        row = list(old_rows[word_id])
        rows.append(row)

    entries_dir = PUBLIC / "entries"
    for old_chunk in entries_dir.glob("*.json"):
        old_chunk.unlink()
    chunk_size = 100
    for start in range(0, len(entries), chunk_size):
        chunk = entries[start : start + chunk_size]
        (entries_dir / f"{start // chunk_size}.json").write_text(
            json.dumps(chunk, ensure_ascii=False, separators=(",", ":")), encoding="utf-8"
        )

    index = dict(old_index)
    index.update(
        {
            "id": "junior-english-textbook",
            "version": 1,
            "name": "初中专属词光",
            "count": len(rows),
            "examples": sum(len(entry["ex"]) for entry in entries),
            "illustrated": sum(bool(row[6] & 1) for row in rows),
            "voiced": sum(bool(row[6] & 2) for row in rows),
            "chunk": chunk_size,
            "words": rows,
        }
    )
    (PUBLIC / "index.json").write_text(json.dumps(index, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    (DATA / "word-atlas.json").write_text(json.dumps(entries, ensure_ascii=False, indent=1), encoding="utf-8")

    with (DATA / "word-atlas.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["id", "word", "ipa_uk", "ipa_us", "cefr", "topic", "meanings_zh", "example1_en", "example1_zh", "example2_en", "example2_zh"])
        for entry in entries:
            examples = entry["ex"] + [{"en": "", "zh": ""}] * 2
            writer.writerow([
                entry["id"], entry["w"], entry["uk"], entry["us"], entry["cefr"], entry["topic"],
                " | ".join(f'{sense["pos"]} {sense["zh"]}'.strip() for sense in entry["senses"]),
                examples[0]["en"], examples[0]["zh"], examples[1]["en"], examples[1]["zh"],
            ])

    if prune_media:
        keep = set(ordered)
        for directory, suffix in (
            (PUBLIC / "img", ".webp"),
            (PUBLIC / "thumb", ".webp"),
            (PUBLIC / "audio/uk", ".mp3"),
            (PUBLIC / "audio/us", ".mp3"),
            (PUBLIC / "audio/ex", ".mp3"),
            (PUBLIC / "audio/ex2", ".mp3"),
        ):
            for path in directory.glob(f"*{suffix}"):
                if path.stem not in keep:
                    path.unlink()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--prune-media", action="store_true")
    args = parser.parse_args()
    if args.prune_media and not args.apply:
        parser.error("--prune-media requires --apply")

    entries = json.loads((DATA / "word-atlas.json").read_text(encoding="utf-8"))
    atlas_entries = {entry["id"]: entry for entry in entries}
    atlas_words = {normalize(entry["w"]): entry["id"] for entry in entries}
    atlas_original = {entry["id"]: entry["w"] for entry in entries}
    matched, unmatched = extract(atlas_words, atlas_original)
    ordered = write_audit(matched, unmatched, atlas_entries)
    summary = json.loads(SUMMARY_JSON.read_text(encoding="utf-8"))
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if args.apply:
        build_dataset(ordered, atlas_entries, args.prune_media)
        print(f"BUILT: {len(ordered)} words; prune_media={args.prune_media}")
    else:
        print("ANALYSIS_ONLY: official dataset unchanged")


if __name__ == "__main__":
    main()
