#!/usr/bin/env python3
"""Verify that the fixed patch ledger still matches its audit正本 files."""

from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / "work" / "statement-label-audit-20260821"
DATA = ROOT / "data"


def read(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def main() -> None:
    official = read(WORK / "official_source_verification.csv")
    candidates = read(WORK / "correction_candidates.csv")
    ledger = read(DATA / "statement_label_corrections.csv")
    confirmed = {row["qId"]: row for row in official if row.get("status") == "confirmed_missing"}
    candidate_by_id = {row["qId"]: row for row in candidates}
    ledger_by_id = {row["qId"]: row for row in ledger}
    assert len(confirmed) == 51
    assert len(candidate_by_id) == 51
    assert len(ledger_by_id) == 51
    assert set(confirmed) == set(candidate_by_id) == set(ledger_by_id)
    assert "R6takken-028" not in ledger_by_id
    assert "R3atakken-038" not in ledger_by_id
    assert "R3btakken-038" not in ledger_by_id
    for q_id, row in ledger_by_id.items():
        official_row = confirmed[q_id]
        candidate = candidate_by_id[q_id]
        assert row["official_source_url"] == official_row["official_source_url"]
        assert row["official_pdf_sha256"] == official_row["official_pdf_sha256"]
        assert row["pdf_page_1based"] == official_row["pdf_page_1based"]
        assert row["expected_label_sequence"] == official_row["label_sequence"]
        assert row["source_ref"] == candidate["source_ref"]
        assert row["source_hash"] == candidate["source_hash"]
        assert row["expected_before_stem_sha256"] == candidate["canonical_stem_hash"]
        assert row["status"] == "approved_label_only_patch"
    print({"ok": True, "ledgerRows": len(ledger), "officialConfirmedMissing": len(confirmed), "blockedExcluded": "R6takken-028"})


if __name__ == "__main__":
    main()
