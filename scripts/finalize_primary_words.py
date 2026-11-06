#!/usr/bin/env python3
"""Normalize primary-school forms and append the genuinely missing headwords."""

from __future__ import annotations

import argparse
import csv
import html
import json
import re
import shutil
import subprocess
import tarfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
PUBLIC = ROOT / "public" / "atlas"
SOURCE = DATA / "primary-source"
CURRENT_COUNT = 1907
OFFICIAL_EXTRA = "lick"
CUSTOM_PREFIX = "primary-"
MEDIA = (
    (1, "img", ".webp"),
    (1, "thumb", ".webp"),
    (2, "audio/uk", ".mp3"),
    (4, "audio/us", ".mp3"),
    (8, "audio/ex", ".mp3"),
    (16, "audio/ex2", ".mp3"),
)

FORM_TO_LEMMA = {
    "drinking": "drink",
    "inspiring": "inspire",
    "jumping": "jump",
    "playing": "play",
    "sleeping": "sleep",
    "ate": "eat",
    "bigger": "big",
    "bought": "buy",
    "cleaned": "clean",
    "could": "can",
    "drank": "drink",
    "faster": "fast",
    "fell": "fall",
    "felt": "feel",
    "heavier": "heavy",
    "laughed": "laugh",
    "licked": "lick",
    "longer": "long",
    "older": "old",
    "rode": "ride",
    "shorter": "short",
    "slept": "sleep",
    "smaller": "small",
    "smarter": "smart",
    "stayed": "stay",
    "stronger": "strong",
    "taller": "tall",
    "thinner": "thin",
    "took": "take",
    "washed": "wash",
    "watched": "watch",
    "woke": "wake",
    "younger": "young",
}

SPECIAL_TO_CUSTOM = {
    "has": "have",
    "had": "have",
    "went": "go",
    "was": "be",
}

A2_WORDS = {
    "chore",
    "hard-working",
    "labour",
    "rsvp",
    "thirtieth",
    "twentieth",
    "twenty-first",
    "twenty-third",
    "gala",
    "gingerbread",
    "marathon",
    "mars",
    "reuse",
    "rover",
    "taikonaut",
    "unplug",
    "cheetah",
    "ice-skate",
    "kilogram",
    "mule",
    "turpan",
}


def git_json(repo: Path, path: str):
    return json.loads(subprocess.check_output(["git", "show", f"origin/main:{path}"], cwd=repo))


def slug(word: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", word.lower()).strip("-")


def custom_id(word: str) -> str:
    return f"{CUSTOM_PREFIX}{slug(word)}"


def extract_official_media(repo: Path, word_id: str, media: int) -> int:
    paths = [f"public/atlas/{folder}/{word_id}{suffix}" for bit, folder, suffix in MEDIA if media & bit]
    proc = subprocess.Popen(["git", "archive", "--format=tar", "origin/main", *paths], cwd=repo, stdout=subprocess.PIPE)
    assert proc.stdout is not None
    with tarfile.open(fileobj=proc.stdout, mode="r|") as archive:
        archive.extractall(ROOT)
    if proc.wait() != 0:
        raise RuntimeError("git archive failed while extracting official media")
    return len(paths)


def svg_for(item: dict, index: int) -> str:
    palettes = [
        ("#F4E8D2", "#D87A55", "#334A5E"),
        ("#E7EFE6", "#6F9477", "#C78E48"),
        ("#E7ECF3", "#557A9F", "#D49A3E"),
        ("#F2E5E7", "#A7677B", "#6D7C65"),
        ("#EAE5D7", "#C39A48", "#43566E"),
    ]
    bg, accent, ink = palettes[index % len(palettes)]
    emoji = html.escape(item["emoji"])
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1024" height="1024" viewBox="0 0 1024 1024">
<defs>
  <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop stop-color="{bg}"/><stop offset="1" stop-color="#FFF9EE"/></linearGradient>
  <filter id="shadow" x="-30%" y="-30%" width="160%" height="160%"><feDropShadow dx="0" dy="24" stdDeviation="24" flood-color="#223044" flood-opacity=".16"/></filter>
</defs>
<rect width="1024" height="1024" rx="96" fill="url(#bg)"/>
<circle cx="154" cy="152" r="76" fill="{accent}" opacity=".22"/>
<circle cx="882" cy="220" r="130" fill="{ink}" opacity=".08"/>
<path d="M70 780 C250 670 350 870 530 742 S810 640 970 740 V1024 H70Z" fill="{accent}" opacity=".18"/>
<path d="M0 854 C210 760 370 970 610 826 S880 780 1024 840 V1024 H0Z" fill="{ink}" opacity=".10"/>
<g filter="url(#shadow)"><circle cx="512" cy="492" r="292" fill="#FFFDF8" opacity=".94"/><circle cx="512" cy="492" r="278" fill="none" stroke="{accent}" stroke-width="8" opacity=".48"/></g>
<text x="512" y="600" text-anchor="middle" font-size="310" font-family="Apple Color Emoji, Segoe UI Emoji, Noto Color Emoji, sans-serif">{emoji}</text>
<g fill="{ink}" opacity=".42"><circle cx="226" cy="864" r="13"/><circle cx="268" cy="864" r="7"/><circle cx="310" cy="864" r="13"/></g>
</svg>'''


def write_custom_images(items: list[dict]) -> None:
    (PUBLIC / "img").mkdir(parents=True, exist_ok=True)
    (PUBLIC / "thumb").mkdir(parents=True, exist_ok=True)
    for index, item in enumerate(items):
        word_id = custom_id(item["w"])
        art = svg_for(item, index)
        (PUBLIC / "img" / f"{word_id}.svg").write_text(art, encoding="utf-8")
        (PUBLIC / "thumb" / f"{word_id}.svg").write_text(art, encoding="utf-8")


def write_csv(entries: list[dict]) -> None:
    with (DATA / "word-atlas.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(["id", "word", "ipa_uk", "ipa_us", "cefr", "topic", "meanings_zh", "example1_en", "example1_zh", "example2_en", "example2_zh"])
        for entry in entries:
            examples = entry["ex"] + [{"en": "", "zh": ""}] * 2
            writer.writerow([
                entry["id"], entry["w"], entry["uk"], entry["us"], entry["cefr"], entry["topic"],
                " | ".join(f'{sense["pos"]} {sense["zh"]}'.strip() for sense in entry["senses"]),
                examples[0]["en"], examples[0]["zh"], examples[1]["en"], examples[1]["zh"],
            ])


def append_family(entry: dict, form: str) -> None:
    label = f"{form} (小学教材词形)"
    if not any(x.lower().startswith(f"{form.lower()} ") or x.lower() == form.lower() for x in entry["fam"]):
        entry["fam"].append(label)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--official-repo", type=Path, required=True)
    args = parser.parse_args()

    entries = json.loads((DATA / "word-atlas.json").read_text(encoding="utf-8"))
    index = json.loads((PUBLIC / "index.json").read_text(encoding="utf-8"))
    if len(entries) != CURRENT_COUNT or index["count"] != CURRENT_COUNT:
        raise RuntimeError(f"expected the published {CURRENT_COUNT}-word dataset")

    custom = json.loads((SOURCE / "小学教材自建词条.json").read_text(encoding="utf-8"))
    if len(custom) != 88 or len({x["w"].lower() for x in custom}) != 88:
        raise RuntimeError("expected 88 unique custom primary headwords")

    official_entries = git_json(args.official_repo, "data/word-atlas.json")
    official_index = git_json(args.official_repo, "public/atlas/index.json")
    official_by_id = {entry["id"]: entry for entry in official_entries}
    official_row_by_id = {row[0]: row for row in official_index["words"]}

    if OFFICIAL_EXTRA in {entry["id"] for entry in entries}:
        raise RuntimeError(f"{OFFICIAL_EXTRA} already exists")
    lick = dict(official_by_id[OFFICIAL_EXTRA])
    lick_row = list(official_row_by_id[OFFICIAL_EXTRA])
    lick["m"] = lick_row[6]
    entries.append(lick)
    index["words"].append(lick_row)
    official_media = extract_official_media(args.official_repo, OFFICIAL_EXTRA, lick_row[6])

    by_word = {entry["w"].lower(): entry for entry in entries}
    for form, lemma in FORM_TO_LEMMA.items():
        target = by_word.get(lemma)
        if not target:
            raise RuntimeError(f"missing lemma for {form}: {lemma}")
        append_family(target, form)

    topic_index = {row[0]: i for i, row in enumerate(index["topics"])}
    cefr_index = {name: i for i, name in enumerate(index["cefr"])}
    custom_entries = []
    custom_rows = []
    for item in custom:
        word_id = custom_id(item["w"])
        if word_id in {entry["id"] for entry in entries}:
            raise RuntimeError(f"duplicate custom id: {word_id}")
        level = "A2" if item["w"].lower() in A2_WORDS else "A1"
        entry = {
            "w": item["w"],
            "uk": item["ipa"],
            "us": item["ipa"],
            "senses": [{"pos": item["pos"], "zh": item["zh"], "en": ""}],
            "ex": [{"en": pair[0].replace("\u200b", ""), "zh": pair[1]} for pair in item["ex"]],
            "col": item.get("col", []),
            "fam": item.get("fam", []),
            "syn": [],
            "ant": [],
            "tip": "小学教材补充词：先听发音，再结合例句理解，最后用这个词说一句自己的话。",
            "cefr": level,
            "topic": item["topic"],
            "note": "依据小学教材词表整理；释义、例句与插画为本站补充内容，不属于词光官方原词条。",
            "id": word_id,
            "m": 1,
        }
        custom_entries.append(entry)
        custom_rows.append([
            word_id,
            item["w"],
            f'{item["pos"]} {item["zh"]}',
            item["ipa"],
            cefr_index[level],
            topic_index[item["topic"]],
            1,
        ])

    entries.extend(custom_entries)
    index["words"].extend(custom_rows)
    write_custom_images(custom)

    chunks = PUBLIC / "entries"
    for old in chunks.glob("*.json"):
        old.unlink()
    for start in range(0, len(entries), index["chunk"]):
        (chunks / f'{start // index["chunk"]}.json').write_text(
            json.dumps(entries[start : start + index["chunk"]], ensure_ascii=False, separators=(",", ":")),
            encoding="utf-8",
        )

    index.update({
        "count": len(entries),
        "examples": sum(len(entry["ex"]) for entry in entries),
        "illustrated": sum(bool(row[6] & 1) for row in index["words"]),
        "voiced": sum(bool(row[6] & 2) for row in index["words"]),
    })
    (PUBLIC / "index.json").write_text(json.dumps(index, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    (DATA / "word-atlas.json").write_text(json.dumps(entries, ensure_ascii=False, indent=1), encoding="utf-8")
    write_csv(entries)

    unmatched = SOURCE / "小学新增_未匹配词光官方词条.csv"
    with unmatched.open(encoding="utf-8-sig", newline="") as handle:
        raw_words = [row["headword"] for row in csv.DictReader(handle) if row["kind"] == "单词"]
    if len(raw_words) != 124:
        raise RuntimeError(f"expected 124 unmatched single words, got {len(raw_words)}")

    custom_words = {item["w"].lower() for item in custom}
    audit_rows = []
    for word in raw_words:
        lower = word.lower()
        if lower in FORM_TO_LEMMA:
            lemma = FORM_TO_LEMMA[lower]
            action = "归入官方原形词"
            target = OFFICIAL_EXTRA if lemma == OFFICIAL_EXTRA else next(entry["id"] for entry in entries if entry["w"].lower() == lemma)
        elif lower in SPECIAL_TO_CUSTOM:
            lemma = SPECIAL_TO_CUSTOM[lower]
            action = "归入小学自建原形词"
            target = custom_id(lemma)
        elif lower in custom_words:
            action = "新增小学自建词条"
            target = custom_id(word)
        else:
            raise RuntimeError(f"unclassified primary word: {word}")
        audit_rows.append([word, action, target])

    with (SOURCE / "小学124词归并结果.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["教材原词", "处理方式", "最终词条ID"])
        writer.writerows(audit_rows)

    summary = {
        "source_single_words": len(raw_words),
        "forms_merged_into_official_lemmas": len(FORM_TO_LEMMA),
        "special_forms_merged_into_custom_lemmas": len(SPECIAL_TO_CUSTOM),
        "official_entry_added": 1,
        "custom_entries_added": len(custom_entries),
        "new_site_entries": 1 + len(custom_entries),
        "primary_section_count": 450 + 1 + len(custom_entries),
        "combined_site_count": len(entries),
        "official_media_files_added": official_media,
        "custom_audio": "device speech synthesis (en-GB/en-US)",
    }
    (SOURCE / "小学124词归并摘要.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
