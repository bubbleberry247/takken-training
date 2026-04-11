#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(r"C:/tmp/kakomon/sekisanshi")
BASE_CSV = BASE_DIR / "sekisan_all_649.csv"
H25_R2_CSV = BASE_DIR / "sekisan_H25_R4_merged.csv"
R3_R4_CSV = BASE_DIR / "sekisan_R3_R4_yomitoku.csv"
R5_R7_CSV = BASE_DIR / "sekisan_R5_R6_R7_structured.csv"
R3_R4_FIX_JSON = BASE_DIR / "sekisan_r3r4_review_fix.json"
DEFAULT_VISION_JSONL = BASE_DIR / "sekisan_vision_gpt54.jsonl"
DEFAULT_OUTPUT_CSV = BASE_DIR / "sekisan_all_final.csv"
DEFAULT_REPORT_JSON = BASE_DIR / "sekisan_all_final_report.json"

HEADERS = [
    "qId", "segmentId", "type", "difficulty",
    "tag1", "tag2", "tag3", "lawTag",
    "revisionFlag", "conceptId", "variantGroupId", "source_ref",
    "imageUrl", "choiceImageUrl",
    "stem", "choiceA", "choiceB", "choiceC", "choiceD", "choiceE",
    "explainA", "explainB", "explainC", "explainD", "explainE",
    "correct", "explainShort", "explainLong", "status", "updatedAt",
]

YEAR_ORDER = ["H25", "H26", "H27", "H28", "H29", "H30", "R1", "R2", "R3", "R4", "R5", "R6", "R7"]
REQUIRED_FIELDS = ["stem", "choiceA", "choiceB", "choiceC", "choiceD", "correct", "explainShort"]
CONTENT_FIELDS = ["stem", "choiceA", "choiceB", "choiceC", "choiceD", "correct", "explainShort"]
MANUAL_CORRECT = {
    "H26sekisan-040": "B,C",
    "R2sekisan-013": "B,C",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the final sekisan QuestionBank CSV.")
    parser.add_argument("--vision-jsonl", default=str(DEFAULT_VISION_JSONL))
    parser.add_argument("--output-csv", default=str(DEFAULT_OUTPUT_CSV))
    parser.add_argument("--report-json", default=str(DEFAULT_REPORT_JSON))
    return parser.parse_args()


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def load_review_corrections(path: Path) -> dict[str, dict[str, str]]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    corrections = payload.get("corrections", {})
    return {qid: value for qid, value in corrections.items() if isinstance(value, dict)}


def load_vision_rows(path: Path) -> dict[str, dict[str, str]]:
    if not path.exists():
        return {}
    rows: dict[str, dict[str, str]] = {}
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            rows[row["qId"]] = row
    return rows


def qid_parts(qid: str) -> tuple[str, int]:
    year, page = qid.split("sekisan-")
    return year, int(page)


def year_sort_index(year: str) -> int:
    return YEAR_ORDER.index(year)


def qid_sort_key(qid: str) -> tuple[int, int]:
    year, page = qid_parts(qid)
    return year_sort_index(year), page


def normalize_text(value: str) -> str:
    text = (value or "").strip()
    if not text:
        return ""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def question_section(page: int) -> tuple[str, str]:
    if page <= 25:
        return "sekisan_I", "Ⅰ建築一般"
    return "sekisan_II", "Ⅱ数量積算"


def normalize_metadata(row: dict[str, str], qid: str) -> None:
    year, page = qid_parts(qid)
    segment_id, primary_tag = question_section(page)
    row["qId"] = qid
    row["segmentId"] = segment_id
    row["type"] = "knowledge"
    row["difficulty"] = row.get("difficulty") or "3"
    row["tag1"] = row.get("tag1") or primary_tag
    row["tag2"] = row.get("tag2") or year
    row["tag3"] = row.get("tag3") or ""
    row["source_ref"] = row.get("source_ref") or f"BSIJ公式 {year}"
    row["status"] = "published"
    row["updatedAt"] = datetime.now().strftime("%Y-%m-%d")


def overlay_fields(target: dict[str, str], source: dict[str, str], fields: list[str]) -> None:
    for field in fields:
        value = normalize_text(source.get(field, ""))
        if value:
            target[field] = value


def build_row_map(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    result: dict[str, dict[str, str]] = {}
    for row in rows:
        clean = {header: row.get(header, "") for header in HEADERS}
        result[row["qId"]] = clean
    return result


def ensure_row(row_map: dict[str, dict[str, str]], qid: str) -> dict[str, str]:
    row = row_map.get(qid)
    if row is None:
        row = {header: "" for header in HEADERS}
        row["qId"] = qid
        row_map[qid] = row
    return row


def all_expected_qids() -> list[str]:
    qids: list[str] = []
    for year in YEAR_ORDER:
        for page in range(1, 51):
            qids.append(f"{year}sekisan-{page:03d}")
    return qids


def validate(row_map: dict[str, dict[str, str]]) -> dict[str, object]:
    missing_rows = [qid for qid in all_expected_qids() if qid not in row_map]
    field_missing: dict[str, list[str]] = {field: [] for field in REQUIRED_FIELDS}
    for qid, row in row_map.items():
        for field in REQUIRED_FIELDS:
            if not normalize_text(row.get(field, "")):
                field_missing[field].append(qid)
    status_counts = Counter((row.get("status") or "") for row in row_map.values())
    type_counts = Counter((row.get("type") or "") for row in row_map.values())
    return {
        "row_count": len(row_map),
        "missing_rows": missing_rows,
        "missing_required_fields": field_missing,
        "status_counts": dict(status_counts),
        "type_counts": dict(type_counts),
    }


def main() -> None:
    args = parse_args()
    base_rows = read_csv_rows(BASE_CSV)
    h25_r2_rows = read_csv_rows(H25_R2_CSV)
    r3_r4_rows = read_csv_rows(R3_R4_CSV)
    r5_r7_rows = read_csv_rows(R5_R7_CSV)
    review_fixes = load_review_corrections(R3_R4_FIX_JSON)
    vision_rows = load_vision_rows(Path(args.vision_jsonl))

    row_map = build_row_map(base_rows)

    for source_rows in [h25_r2_rows, r3_r4_rows, r5_r7_rows]:
        for source in source_rows:
            qid = source["qId"]
            row = ensure_row(row_map, qid)
            overlay_fields(row, source, HEADERS)

    for qid, fix in review_fixes.items():
        row = ensure_row(row_map, qid)
        overlay_fields(row, fix, CONTENT_FIELDS)

    for qid, vision in vision_rows.items():
        row = ensure_row(row_map, qid)
        overlay_fields(row, vision, ["stem", "choiceA", "choiceB", "choiceC", "choiceD", "correct", "explainShort"])

    for qid, correct in MANUAL_CORRECT.items():
        row = ensure_row(row_map, qid)
        row["correct"] = correct

    for qid, row in row_map.items():
        normalize_metadata(row, qid)
        for field in CONTENT_FIELDS:
            row[field] = normalize_text(row.get(field, ""))

    ordered_qids = sorted(row_map, key=qid_sort_key)
    output_csv = Path(args.output_csv)
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with output_csv.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=HEADERS)
        writer.writeheader()
        for qid in ordered_qids:
            writer.writerow({header: row_map[qid].get(header, "") for header in HEADERS})

    report = validate(row_map)
    report["vision_rows_used"] = sorted(vision_rows.keys())
    report["review_fix_count"] = len(review_fixes)
    report["output_csv"] = str(output_csv)

    report_path = Path(args.report_json)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Wrote CSV: {output_csv}")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
