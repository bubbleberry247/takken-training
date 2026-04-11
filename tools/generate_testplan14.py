"""
Generate TestPlan14 CSV for doboku-14w-training.

This output is intended to match:
  C:\\ProgramData\\Generative AI\\Github\\doboku-14w-training\\src\\db.gs
  HEADERS[SHEETS.TestPlan14]

Columns:
  testIndex,label,targetSegments,questionsPerTest,abilityCount,revisionMinCount,unlockWeek,notes
"""

from __future__ import annotations

import csv
from pathlib import Path


HEADERS = [
    "testIndex",
    "label",
    "targetSegments",
    "questionsPerTest",
    "abilityCount",
    "revisionMinCount",
    "unlockWeek",
    "notes",
]


DEFAULT_ROWS = [
    [1, "第1回 R7 学科A", "R7gakkaA", 30, 4, 2, 0, ""],
    [2, "第2回 R7 学科B", "R7gakkaB", 30, 4, 2, 1, ""],
    [3, "第3回 R6 学科A", "R6gakkaA", 30, 4, 2, 2, ""],
    [4, "第4回 R6 学科B", "R6gakkaB", 30, 4, 2, 3, ""],
    [5, "第5回 R5 学科A", "R5gakkaA", 30, 4, 2, 4, ""],
    [6, "第6回 R5 学科B", "R5gakkaB", 30, 4, 2, 5, ""],
    [7, "第7回 R4 学科A", "R4gakkaA", 30, 4, 2, 6, ""],
    [8, "第8回 R4 学科B", "R4gakkaB", 30, 4, 2, 7, ""],
    [9, "第9回 R3 学科A", "R3gakkaA", 30, 4, 2, 8, ""],
    [10, "第10回 R3 学科B", "R3gakkaB", 30, 4, 2, 9, ""],
    [11, "第11回 R2 学科A", "R2gakkaA", 30, 4, 2, 10, ""],
    [12, "第12回 R2 学科B", "R2gakkaB", 30, 4, 2, 11, ""],
    [13, "第13回 R1 学科A", "R1gakkaA", 30, 4, 2, 12, ""],
    [14, "第14回 R1 学科B", "R1gakkaB", 30, 4, 2, 13, ""],
]


def generate_testplan14(output_csv: Path) -> None:
    # Use UTF-8 with BOM for compatibility with Google Sheets/Excel imports.
    with output_csv.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(HEADERS)
        w.writerows(DEFAULT_ROWS)

    print(f"Saved: {output_csv}")
    print(f"Rows: {len(DEFAULT_ROWS)} (excluding header)")


def main() -> None:
    output_path = Path(__file__).with_name("testplan14.csv")
    generate_testplan14(output_path)


if __name__ == "__main__":
    main()
