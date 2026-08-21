#!/usr/bin/env python3
"""Apply or verify the fixed 51-question label-only source correction.

The ledger is the allowlist.  This tool changes only ``stem`` in the tracked
canonical CSV; it never touches choices, answers, explanations, IDs, or the
blocked R6takken-028 record.  ``--apply`` requires an explicit target count
and qId approval so an accidental broader source rewrite fails closed.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data" / "takken_all_final.csv"
LEDGER = ROOT / "data" / "statement_label_corrections.csv"
HEADERS = None
BLOCKED_QIDS = {"R6takken-028"}
FORBIDDEN_QIDS = {"R3atakken-038", "R3btakken-038"}


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def canonical_text(value: str) -> str:
    return (value or "").replace("\r\n", "\n").replace("\r", "\n")


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def corrected_stem(row: dict[str, str], spec: dict[str, str]) -> str:
    stem = canonical_text(row.get("stem", ""))
    if sha(stem) != spec["expected_before_stem_sha256"]:
        raise ValueError(f"expected-before stem hash mismatch: {spec['qId']}")
    offsets = [int(value) for value in spec["insertion_offsets"].split(";") if value]
    labels = spec["expected_label_sequence"].split("・")
    if len(offsets) != len(labels) or len(offsets) != int(spec["source_statement_count"]):
        raise ValueError(f"offset/label count mismatch: {spec['qId']}")
    corrected = stem
    for offset, label in sorted(zip(offsets, labels), reverse=True):
        if offset < 0 or offset > len(stem):
            raise ValueError(f"insertion offset out of range: {spec['qId']}")
        corrected = corrected[:offset] + "\n\n" + label + "\u3000" + corrected[offset:]
    if sha(corrected) != spec["replacement_stem_sha256"]:
        raise ValueError(f"replacement stem hash mismatch: {spec['qId']}")
    return corrected


def validate_schema(headers: list[str], label: str) -> None:
    if not headers or headers[0] != "qId" or "stem" not in headers:
        raise ValueError(f"unexpected CSV schema in {label}")


def validate_rows(rows: list[dict[str, str]], specs: list[dict[str, str]], state: str) -> dict[str, int]:
    by_id = {row.get("qId", ""): row for row in rows}
    if len(by_id) != len(rows) or any(not q_id for q_id in by_id):
        raise ValueError("canonical qId inventory is not unique/nonblank")
    spec_ids = {spec["qId"] for spec in specs}
    if len(specs) != 51 or len(spec_ids) != 51:
        raise ValueError("statement label ledger must contain exactly 51 unique qIds")
    if spec_ids & BLOCKED_QIDS or spec_ids & FORBIDDEN_QIDS:
        raise ValueError("blocked or Q38 qId is present in statement label ledger")
    counts = {"before": 0, "after": 0}
    for spec in specs:
        q_id = spec["qId"]
        row = by_id.get(q_id)
        if row is None:
            raise ValueError(f"ledger qId is missing from canonical source: {q_id}")
        stem = canonical_text(row.get("stem", ""))
        before = sha(stem) == spec["expected_before_stem_sha256"]
        after = sha(stem) == spec["replacement_stem_sha256"]
        if before:
            counts["before"] += 1
        elif after:
            counts["after"] += 1
        else:
            raise ValueError(f"qId is neither expected before nor replacement state: {q_id}")
        if state == "before" and not before:
            raise ValueError(f"expected pre-patch state but found replacement: {q_id}")
        if state == "after" and not after:
            raise ValueError(f"expected corrected state but found old/unknown: {q_id}")
    if state == "before" and counts["before"] != 51:
        raise ValueError(f"expected 51 before rows, got {counts['before']}")
    if state == "after" and counts["after"] != 51:
        raise ValueError(f"expected 51 corrected rows, got {counts['after']}")
    return counts


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="write the 51 approved stem edits")
    parser.add_argument("--expected-target-count", type=int)
    parser.add_argument("--approve-qids")
    parser.add_argument("--check-before", action="store_true", help="verify the unpatched source state")
    args = parser.parse_args()

    source_headers, source_rows = read_csv(SOURCE)
    ledger_headers, specs = read_csv(LEDGER)
    validate_schema(source_headers, "canonical source")
    required_ledger = {"qId", "expected_before_stem_sha256", "replacement_stem_sha256", "expected_label_sequence", "insertion_offsets", "source_statement_count"}
    if not required_ledger.issubset(set(ledger_headers)):
        raise ValueError("statement label ledger schema is incomplete")
    state = "before" if args.check_before else "after" if not args.apply else "before"
    counts = validate_rows(source_rows, specs, state)
    if not args.apply:
        print({"rows": len(specs), "state": state, "before": counts["before"], "after": counts["after"], "check": "ok"})
        return

    if args.expected_target_count != 51 or not args.approve_qids:
        raise ValueError("--apply requires --expected-target-count 51 and --approve-qids")
    approved = {q_id.strip() for q_id in args.approve_qids.split(",") if q_id.strip()}
    ledger_ids = {spec["qId"] for spec in specs}
    if approved != ledger_ids:
        raise ValueError("approved qIds do not exactly match the 51-row ledger")

    by_spec = {spec["qId"]: spec for spec in specs}
    changed_cells = 0
    for row in source_rows:
        spec = by_spec.get(row.get("qId", ""))
        if spec is None:
            continue
        row["stem"] = corrected_stem(row, spec)
        changed_cells += 1
    validate_rows(source_rows, specs, "after")

    temp = SOURCE.with_suffix(SOURCE.suffix + ".statement-label.tmp")
    with temp.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=source_headers, lineterminator="\r\n")
        writer.writeheader()
        writer.writerows(source_rows)
    temp.replace(SOURCE)
    print({"rows": len(specs), "changedStemCells": changed_cells, "state": "after", "apply": True})


if __name__ == "__main__":
    main()
