"""Convert parsed JSON (from parse_questions.py) to QuestionBank CSV.

Input JSON format:
  {
    "R7gakkaA": [ {"qNum": 1, "stem": "...", "choices": {"1": "..."}, "correct": 3}, ...],
    "R7gakkaB": [ ... ],
    ...
  }

Output CSV columns are aligned to:
  C:\\ProgramData\\Generative AI\\Github\\doboku-14w-training\\src\\db.gs
  HEADERS[SHEETS.QuestionBank]

Usage:
  python convert_to_questionbank.py --input questions_parsed.json --output questionbank_complete.csv

Notes:
- segmentId is set to the JSON key (e.g. R7gakkaA)
- qId is generated as "{segmentId}-{qNum:03d}"
- type defaults to "knowledge"
- If a choice text is missing/blank, a placeholder like "（図1）" is inserted so the question passes validation.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List


SEGMENT_RE = re.compile(r"^(R\d+)gakka([AB])$", re.IGNORECASE)


def _now_iso() -> str:
    return datetime.now().replace(microsecond=0).isoformat()


def _clean_text(text: Any) -> str:
    s = "" if text is None else str(text)
    # Collapse whitespace while keeping typical Japanese punctuation.
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def _choice_placeholder(choice_num: int) -> str:
    # Use numeric placeholder to match original (1)-(4) style.
    return f"（図{choice_num}）"


def _answer_num_to_letter(n: Any) -> str:
    try:
        i = int(n)
    except Exception:
        return ""
    return {1: "A", 2: "B", 3: "C", 4: "D", 5: "E"}.get(i, "")


def convert_to_questionbank(parsed: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    ts = _now_iso()

    for seg_key in sorted(parsed.keys()):
        seg = seg_key.strip()
        if not SEGMENT_RE.match(seg):
            # Still allow import, but segmentId must align with TestPlan14.
            print(f"Warning: unexpected segment key: {seg!r}")

        questions = parsed.get(seg_key) or []
        for q in questions:
            q_num = int(q.get("qNum") or 0)
            q_id = f"{seg}-{q_num:03d}"

            choices_in = q.get("choices") or {}

            def get_choice(num: int) -> str:
                # keys may be "1" or 1
                v = choices_in.get(str(num))
                if v is None:
                    v = choices_in.get(num)
                s = _clean_text(v)
                if not s:
                    s = _choice_placeholder(num)
                return s

            choice_a = get_choice(1)
            choice_b = get_choice(2)
            choice_c = get_choice(3)
            choice_d = get_choice(4)

            # Choice E is optional; keep blank unless explicitly present.
            raw_e = choices_in.get("5") if "5" in choices_in else choices_in.get(5)
            choice_e = _clean_text(raw_e)

            correct_letter = _answer_num_to_letter(q.get("correct"))

            # Minimal source_ref for traceability
            m = SEGMENT_RE.match(seg)
            if m:
                year = m.group(1).upper()
                gakka = m.group(2).upper()
                source_ref = f"{year} 学科{gakka} No.{q_num}"
            else:
                source_ref = f"{seg} No.{q_num}"

            row: Dict[str, str] = {
                "qId": q_id,
                "segmentId": seg,
                "type": "knowledge",
                "difficulty": "3",
                "tag1": "",
                "tag2": "",
                "tag3": "",
                "lawTag": "",
                "revisionFlag": "0",
                "conceptId": "",
                "variantGroupId": "",
                "source_ref": source_ref,
                "imageUrl": "",
                "stem": _clean_text(q.get("stem")),
                "choiceA": choice_a,
                "choiceB": choice_b,
                "choiceC": choice_c,
                "choiceD": choice_d,
                "choiceE": choice_e,
                "explainA": "",
                "explainB": "",
                "explainC": "",
                "explainD": "",
                "explainE": "",
                "correct": correct_letter,
                "explainShort": "",
                "explainLong": "",
                "status": "published" if correct_letter else "draft",
                "updatedAt": ts,
            }

            rows.append(row)

    return rows


def write_csv(rows: List[Dict[str, str]], output_csv: Path) -> None:
    fieldnames = [
        "qId",
        "segmentId",
        "type",
        "difficulty",
        "tag1",
        "tag2",
        "tag3",
        "lawTag",
        "revisionFlag",
        "conceptId",
        "variantGroupId",
        "source_ref",
        "imageUrl",
        "stem",
        "choiceA",
        "choiceB",
        "choiceC",
        "choiceD",
        "choiceE",
        "explainA",
        "explainB",
        "explainC",
        "explainD",
        "explainE",
        "correct",
        "explainShort",
        "explainLong",
        "status",
        "updatedAt",
    ]

    # UTF-8 with BOM for Google Sheets / Excel import compatibility.
    with output_csv.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)


def main() -> None:
    ap = argparse.ArgumentParser(description="Convert parsed JSON to QuestionBank CSV")
    ap.add_argument("--input", required=True, help="Input JSON (from parse_questions.py)")
    ap.add_argument("--output", default="questionbank_complete.csv", help="Output CSV")
    args = ap.parse_args()

    in_path = Path(args.input)
    out_path = Path(args.output)

    parsed = json.loads(in_path.read_text(encoding="utf-8"))
    rows = convert_to_questionbank(parsed)
    write_csv(rows, out_path)

    total = len(rows)
    published = sum(1 for r in rows if r.get("status") == "published")
    print(f"Saved: {out_path}")
    print(f"Rows: {total} (published: {published})")


if __name__ == "__main__":
    main()
