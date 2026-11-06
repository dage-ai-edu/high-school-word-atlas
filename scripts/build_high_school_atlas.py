#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import re
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PUBLIC_ATLAS = ROOT / "public/atlas"
DATA = ROOT / "data"
STAGE_ORDER = ["初中基础", "高一上", "高一下", "高二", "高三"]
CEFR_BY_STAGE = {"初中基础": "A2", "高一上": "B1", "高一下": "B1", "高二": "B2", "高三": "B2"}
MEDIA = {"img": 1, "uk": 2, "us": 4, "ex": 8, "ex2": 16}


def norm(value: str) -> str:
    value = value.casefold().replace("’", "'")
    return re.sub(r"[^a-z0-9'-]+", "", value)


def slug(value: str) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", value.casefold()).strip("-")
    return base or hashlib.sha1(value.encode("utf-8")).hexdigest()[:12]


def clean_gloss(value: str) -> str:
    value = re.sub(r"^[版编；，、：。\s]+", "", value)
    value = re.sub(r"[（(]\s*$", "", value)
    value = re.sub(r"\s+", "", value)
    return value[:100] or "教材词汇"


def compact_zh(entry: dict) -> str:
    return "；".join(
        f"{sense.get('pos', '')} {sense.get('zh', '')}".strip()
        for sense in entry.get("senses", [])[:3]
    )


def svg_card(word: str, gloss: str, stage: str) -> str:
    digest = hashlib.sha1(word.encode("utf-8")).digest()
    palettes = [
        ("#F4EBDD", "#23304A", "#D97855", "#B9C8AD"),
        ("#E9EEE8", "#24364B", "#C26D4A", "#D4B56A"),
        ("#EEE7F2", "#27304A", "#8B6CB3", "#D99874"),
        ("#E8EFF3", "#223044", "#5E88A3", "#D9A85F"),
    ]
    bg, ink, accent, soft = palettes[digest[0] % len(palettes)]
    initial = html.escape(word[:1].upper())
    safe_word = html.escape(word)
    safe_gloss = html.escape(gloss[:26])
    safe_stage = html.escape(stage)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="768" height="768" viewBox="0 0 768 768">
<rect width="768" height="768" rx="64" fill="{bg}"/>
<circle cx="590" cy="168" r="116" fill="{soft}" opacity=".72"/>
<path d="M86 586 C210 464 354 672 682 486" fill="none" stroke="{accent}" stroke-width="20" stroke-linecap="round" opacity=".75"/>
<path d="M118 622 C272 528 438 716 676 574" fill="none" stroke="{ink}" stroke-width="5" stroke-linecap="round" opacity=".18"/>
<text x="78" y="276" font-size="230" font-family="Georgia,serif" font-weight="700" fill="{ink}">{initial}</text>
<text x="80" y="386" font-size="64" font-family="Georgia,serif" font-weight="700" fill="{ink}">{safe_word}</text>
<text x="82" y="452" font-size="34" font-family="Arial,sans-serif" fill="{ink}" opacity=".72">{safe_gloss}</text>
<rect x="80" y="518" width="150" height="54" rx="27" fill="{accent}"/>
<text x="155" y="556" text-anchor="middle" font-size="28" font-family="Arial,sans-serif" font-weight="700" fill="#fff">{safe_stage}</text>
<text x="80" y="690" font-size="22" font-family="Arial,sans-serif" letter-spacing="4" fill="{ink}" opacity=".45">HIGH SCHOOL WORD ATLAS</text>
</svg>"""


def copy_media(source_atlas: Path, word_id: str, target_id: str | None = None) -> int:
    target_id = target_id or word_id
    flags = 0
    for folder, extensions, bit in [
        ("img", ("webp", "svg"), MEDIA["img"]),
        ("thumb", ("webp", "svg"), 0),
        ("audio/uk", ("mp3",), MEDIA["uk"]),
        ("audio/us", ("mp3",), MEDIA["us"]),
        ("audio/ex", ("mp3",), MEDIA["ex"]),
        ("audio/ex2", ("mp3",), MEDIA["ex2"]),
    ]:
        for ext in extensions:
            source = source_atlas / folder / f"{word_id}.{ext}"
            if not source.exists():
                continue
            target = PUBLIC_ATLAS / folder / f"{target_id}.{ext}"
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            flags |= bit
            break
    return flags


def write_csv(entries: list[dict]) -> None:
    fields = [
        "id", "word", "ipa_uk", "ipa_us", "cefr", "topic", "meanings_zh",
        "example1_en", "example1_zh", "example2_en", "example2_zh",
    ]
    with (DATA / "word-atlas.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for entry in entries:
            examples = entry.get("ex", [])
            writer.writerow(
                {
                    "id": entry["id"],
                    "word": entry["w"],
                    "ipa_uk": entry.get("uk", ""),
                    "ipa_us": entry.get("us", ""),
                    "cefr": entry.get("cefr", ""),
                    "topic": entry.get("topic", ""),
                    "meanings_zh": compact_zh(entry),
                    "example1_en": examples[0]["en"] if len(examples) > 0 else "",
                    "example1_zh": examples[0]["zh"] if len(examples) > 0 else "",
                    "example2_en": examples[1]["en"] if len(examples) > 1 else "",
                    "example2_zh": examples[1]["zh"] if len(examples) > 1 else "",
                }
            )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-csv", required=True, type=Path)
    parser.add_argument("--official-repo", required=True, type=Path)
    parser.add_argument("--junior-repo", required=True, type=Path)
    args = parser.parse_args()

    rows = list(csv.DictReader(args.source_csv.open(encoding="utf-8-sig")))
    rows = [row for row in rows if row["proper_noun_marked"].lower() != "true"]
    rows.sort(key=lambda row: (STAGE_ORDER.index(row["stages"].split("；")[0]), row["word"].casefold()))

    official_entries = json.loads((args.official_repo / "data/word-atlas.json").read_text())
    official = {norm(entry["w"]): entry for entry in official_entries}
    junior_entries = json.loads((args.junior_repo / "data/word-atlas.json").read_text())
    junior = {norm(entry["w"]): entry for entry in junior_entries}
    official_index = json.loads((args.official_repo / "public/atlas/index.json").read_text())
    cefr = official_index["cefr"]
    topics = official_index["topics"]
    topic_index = {key: index for index, (key, _label) in enumerate(topics)}

    if PUBLIC_ATLAS.exists():
        shutil.rmtree(PUBLIC_ATLAS)
    for folder in ["entries", "img", "thumb", "audio/uk", "audio/us", "audio/ex", "audio/ex2"]:
        (PUBLIC_ATLAS / folder).mkdir(parents=True, exist_ok=True)

    entries: list[dict] = []
    index_rows: list[list] = []
    stage_counts = {stage: 0 for stage in STAGE_ORDER}
    official_count = 0
    junior_reused = 0
    custom_count = 0

    for row in rows:
        key = norm(row["word"])
        stage = row["stages"].split("；")[0]
        stage_counts[stage] += 1
        if key in official:
            entry = dict(official[key])
            flags = copy_media(args.official_repo / "public/atlas", entry["id"])
            official_count += 1
        elif key in junior:
            entry = dict(junior[key])
            flags = copy_media(args.junior_repo / "public/atlas", entry["id"])
            junior_reused += 1
        else:
            gloss = clean_gloss(row["textbook_zh_gloss"])
            word_id = f"high-{slug(row['word'])}"
            entry = {
                "w": row["word"],
                "uk": row.get("ipa", "").strip("/"),
                "us": row.get("ipa", "").strip("/"),
                "senses": [{"pos": "", "zh": gloss, "en": ""}],
                "ex": [],
                "col": [],
                "fam": [],
                "syn": [],
                "ant": [],
                "tip": f"教材补充词；首次出现于{stage}，来源：{row['books']}。",
                "cefr": CEFR_BY_STAGE[stage],
                "topic": "education",
                "note": "教材补充词条：中文释义来自教材词汇表；发音使用设备语音。",
                "id": word_id,
            }
            art = svg_card(row["word"], gloss, stage)
            for folder in ("img", "thumb"):
                (PUBLIC_ATLAS / folder / f"{word_id}.svg").write_text(art, encoding="utf-8")
            flags = MEDIA["img"]
            custom_count += 1

        entry["m"] = flags
        entries.append(entry)
        zh = compact_zh(entry)
        index_rows.append(
            [
                entry["id"],
                entry["w"],
                zh,
                entry.get("uk") or entry.get("us") or "",
                cefr.index(entry["cefr"]) if entry["cefr"] in cefr else 2,
                topic_index.get(entry.get("topic", "education"), topic_index.get("education", 0)),
                flags,
            ]
        )

    chunk_size = 200
    for start in range(0, len(entries), chunk_size):
        chunk = entries[start:start + chunk_size]
        (PUBLIC_ATLAS / "entries" / f"{start // chunk_size}.json").write_text(
            json.dumps(chunk, ensure_ascii=False, separators=(",", ":")),
            encoding="utf-8",
        )

    index = {
        "id": "high-school-word-atlas",
        "name": "高中专属词光",
        "kind": "open",
        "count": len(entries),
        "examples": sum(len(entry.get("ex", [])) for entry in entries),
        "illustrated": sum(bool(entry["m"] & MEDIA["img"]) for entry in entries),
        "chunk": chunk_size,
        "topics": topics,
        "cefr": cefr,
        "words": index_rows,
    }
    (PUBLIC_ATLAS / "index.json").write_text(
        json.dumps(index, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )

    DATA.mkdir(parents=True, exist_ok=True)
    (DATA / "word-atlas.json").write_text(
        json.dumps(entries, ensure_ascii=False, indent=1),
        encoding="utf-8",
    )
    write_csv(entries)
    source_dir = DATA / "high-school-source"
    source_dir.mkdir(parents=True, exist_ok=True)
    source_copy = source_dir / args.source_csv.name
    if args.source_csv.resolve() != source_copy.resolve():
        shutil.copy2(args.source_csv, source_copy)
    summary = {
        "total": len(entries),
        "official_word_atlas_entries": official_count,
        "reused_junior_custom_entries": junior_reused,
        "new_textbook_supplement_entries": custom_count,
        "stage_counts": stage_counts,
        "proper_nouns_excluded": len(list(csv.DictReader(args.source_csv.open(encoding="utf-8-sig")))) - len(rows),
    }
    (source_dir / "高中专属词光_构建摘要.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
