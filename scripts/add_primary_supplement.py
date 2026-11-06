#!/usr/bin/env python3
"""Append official Word Atlas entries matched from the primary textbooks."""

from __future__ import annotations

import argparse
import csv
import json
import shutil
import subprocess
import tarfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "public/atlas"
DATA = ROOT / "data"
PRIMARY_COUNT = 450
JUNIOR_COUNT = 1457
MEDIA = (
    (1, "img", ".webp"),
    (1, "thumb", ".webp"),
    (2, "audio/uk", ".mp3"),
    (4, "audio/us", ".mp3"),
    (8, "audio/ex", ".mp3"),
    (16, "audio/ex2", ".mp3"),
)


def git_json(repo: Path, path: str):
    raw = subprocess.check_output(["git", "show", f"origin/main:{path}"], cwd=repo)
    return json.loads(raw)


def extract_media(repo: Path, paths: list[str]) -> None:
    proc = subprocess.Popen(["git", "archive", "--format=tar", "origin/main", *paths], cwd=repo, stdout=subprocess.PIPE)
    assert proc.stdout is not None
    with tarfile.open(fileobj=proc.stdout, mode="r|") as archive:
        archive.extractall(ROOT)
    if proc.wait() != 0:
        raise RuntimeError("git archive failed while extracting official media")


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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--official-repo", type=Path, required=True)
    parser.add_argument("--audit-dir", type=Path, required=True)
    args = parser.parse_args()

    current_entries = json.loads((DATA / "word-atlas.json").read_text(encoding="utf-8"))
    current_index = json.loads((PUBLIC / "index.json").read_text(encoding="utf-8"))
    if len(current_entries) != JUNIOR_COUNT or current_index["count"] != JUNIOR_COUNT:
        raise RuntimeError(f"expected untouched {JUNIOR_COUNT}-word junior dataset")

    official_entries = git_json(args.official_repo, "data/word-atlas.json")
    official_index = git_json(args.official_repo, "public/atlas/index.json")
    if official_index["topics"] != current_index["topics"] or official_index["cefr"] != current_index["cefr"]:
        raise RuntimeError("official and junior index taxonomies differ")

    target_ids = json.loads((args.audit_dir / "小学新增_词光官方ID.json").read_text(encoding="utf-8"))
    if len(target_ids) != PRIMARY_COUNT or len(set(target_ids)) != PRIMARY_COUNT:
        raise RuntimeError(f"expected {PRIMARY_COUNT} unique primary supplement IDs")
    existing_ids = {entry["id"] for entry in current_entries}
    if existing_ids.intersection(target_ids):
        raise RuntimeError("primary supplement overlaps existing junior IDs")

    entry_by_id = {entry["id"]: entry for entry in official_entries}
    row_by_id = {row[0]: row for row in official_index["words"]}
    supplement_entries = []
    supplement_rows = []
    media_paths = []
    for word_id in target_ids:
        entry = dict(entry_by_id[word_id])
        row = list(row_by_id[word_id])
        entry["m"] = row[6]
        supplement_entries.append(entry)
        supplement_rows.append(row)
        for bit, directory, suffix in MEDIA:
            if row[6] & bit:
                media_paths.append(f"public/atlas/{directory}/{word_id}{suffix}")

    combined_entries = current_entries + supplement_entries
    combined_rows = current_index["words"] + supplement_rows
    chunk_size = current_index["chunk"]
    entries_dir = PUBLIC / "entries"
    for old_chunk in entries_dir.glob("*.json"):
        old_chunk.unlink()
    for start in range(0, len(combined_entries), chunk_size):
        chunk = combined_entries[start : start + chunk_size]
        (entries_dir / f"{start // chunk_size}.json").write_text(
            json.dumps(chunk, ensure_ascii=False, separators=(",", ":")), encoding="utf-8"
        )

    index = dict(current_index)
    index.update(
        {
            "count": len(combined_rows),
            "examples": sum(len(entry["ex"]) for entry in combined_entries),
            "illustrated": sum(bool(row[6] & 1) for row in combined_rows),
            "voiced": sum(bool(row[6] & 2) for row in combined_rows),
            "words": combined_rows,
        }
    )
    (PUBLIC / "index.json").write_text(json.dumps(index, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    (DATA / "word-atlas.json").write_text(json.dumps(combined_entries, ensure_ascii=False, indent=1), encoding="utf-8")
    write_csv(combined_entries)
    extract_media(args.official_repo, media_paths)

    audit_target = DATA / "primary-source"
    audit_target.mkdir(parents=True, exist_ok=True)
    for name in (
        "小学新增_匹配词光官方词条.csv",
        "小学新增_未匹配词光官方词条.csv",
        "小学新增_词光官方ID.json",
        "小学新增_词光匹配摘要.json",
    ):
        shutil.copyfile(args.audit_dir / name, audit_target / name)

    result = {
        "junior_unchanged": JUNIOR_COUNT,
        "primary_supplement": len(supplement_entries),
        "combined": len(combined_entries),
        "media_files_added": len(media_paths),
        "second_example_audio": sum(bool(row[6] & 16) for row in supplement_rows),
    }
    (audit_target / "build-summary.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

