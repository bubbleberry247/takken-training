#!/usr/bin/env python3
"""Generate the GAS fixed spec array from the redacted statement ledger."""

from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "data" / "statement_label_corrections.csv"
TARGET = ROOT / "src" / "patchStatementLabels.gs"
MARKER = "var TAKKEN_STATEMENT_LABEL_PATCH_SPECS_ = []"


def main() -> None:
    with LEDGER.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != 51 or len({row["qId"] for row in rows}) != 51:
        raise ValueError("statement label ledger must contain 51 unique rows")
    specs = []
    for row in rows:
        specs.append({
            "qId": row["qId"],
            "expectedBeforeStemSha256": row["expected_before_stem_sha256"],
            "replacementStemSha256": row["replacement_stem_sha256"],
            "expectedLabelSequence": row["expected_label_sequence"],
            "insertionOffsets": [int(value) for value in row["insertion_offsets"].split(";") if value],
            "sourceStatementCount": int(row["source_statement_count"]),
            "officialSourceUrl": row["official_source_url"],
            "officialPdfSha256": row["official_pdf_sha256"],
            "pdfPage": int(row["pdf_page_1based"]),
            "sourceKind": row["source_kind"],
            "sourceRef": row["source_ref"],
            "sourceHash": row["source_hash"],
        })
    original = TARGET.read_text(encoding="utf-8")
    if MARKER not in original:
        raise ValueError("spec placeholder not found")
    replacement = "var TAKKEN_STATEMENT_LABEL_PATCH_SPECS_ = " + json.dumps(specs, ensure_ascii=False, indent=2) + ";"
    TARGET.write_text(original.replace(MARKER + ";", replacement, 1), encoding="utf-8")
    print({"rows": len(specs), "target": str(TARGET)})


if __name__ == "__main__":
    main()
