#!/usr/bin/env python3
"""Verify the 51-row statement-label ledger from tracked, redacted evidence."""

from __future__ import annotations

import copy
import csv
import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "data" / "statement_label_corrections.csv"
EVIDENCE = ROOT / "data" / "release-evidence" / "statement-labels" / "official_verification.json"
EVIDENCE_SHA256 = "d0964b6793386d8245cf498d9c71b2de25360ba96c7f3e581a0c290360b05a8e"
LEDGER_SCHEMA = [
    "qId", "category", "official_source_url", "official_pdf_sha256",
    "pdf_page_1based", "source_kind", "source_ref", "source_hash",
    "expected_before_stem_sha256", "replacement_stem_sha256",
    "expected_label_sequence", "insertion_offsets", "source_statement_count",
    "protected_fields", "status",
]
EVIDENCE_ROW_SCHEMA = [
    "qId", "status", "official_source_url", "official_pdf_sha256",
    "pdf_page_1based", "expected_label_sequence_ascii", "ledger_row_sha256",
]
TOP_LEVEL_SCHEMA = {
    "schemaVersion", "evidenceStatus", "rowCount", "excludedQIds",
    "containsQuestionText", "containsPii", "ledgerHashAlgorithm",
    "labelEncoding", "rowSchema", "rows",
}
EXCLUDED_QIDS = {"R6takken-028", "R3atakken-038", "R3btakken-038"}
LABEL_ASCII = {"ア": "A", "イ": "I", "ウ": "U", "エ": "E"}
SHA256_RE = re.compile(r"[0-9a-f]{64}")


def canonical_text(value: object) -> str:
    return str("" if value is None else value).replace("\r\n", "\n").replace("\r", "\n")


def canonical_evidence_bytes(raw: bytes) -> bytes:
    if raw.startswith(b"\xef\xbb\xbf"):
        raw = raw[3:]
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError("statement-label evidence must be valid UTF-8") from exc
    return canonical_text(text).encode("utf-8")


def read_ledger(path: Path = LEDGER) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        headers = list(reader.fieldnames or [])
        rows = list(reader)
    return headers, rows


def ledger_row_sha256(row: dict[str, str], headers: list[str]) -> str:
    payload = "\x1f".join(f"{header}\x1e{canonical_text(row.get(header, ''))}" for header in headers)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def encoded_labels(value: str) -> str:
    try:
        return ",".join(LABEL_ASCII[label] for label in value.split("・"))
    except KeyError as exc:
        raise ValueError("ledger label sequence contains an unsupported label") from exc


def validate(evidence: dict[str, object], headers: list[str], ledger: list[dict[str, str]]) -> None:
    if set(evidence) != TOP_LEVEL_SCHEMA:
        raise ValueError("statement-label evidence top-level schema mismatch")
    if headers != LEDGER_SCHEMA:
        raise ValueError("statement-label ledger schema mismatch")
    if (evidence["schemaVersion"] != 1 or
            evidence["evidenceStatus"] != "approved_official_source_verification" or
            evidence["rowCount"] != 51 or evidence["containsQuestionText"] is not False or
            evidence["containsPii"] is not False or
            evidence["ledgerHashAlgorithm"] != "sha256(header\\x1evalue joined by \\x1f; CRLF/CR normalized to LF)" or
            evidence["labelEncoding"] != "A=katakana-A,I=katakana-I,U=katakana-U,E=katakana-E" or
            evidence["rowSchema"] != EVIDENCE_ROW_SCHEMA):
        raise ValueError("statement-label evidence fixed contract mismatch")
    if set(evidence["excludedQIds"]) != EXCLUDED_QIDS or len(evidence["excludedQIds"]) != 3:
        raise ValueError("statement-label excluded qId contract mismatch")
    evidence_rows = evidence["rows"]
    if not isinstance(evidence_rows, list) or len(evidence_rows) != 51 or len(ledger) != 51:
        raise ValueError("statement-label evidence/ledger must contain exactly 51 rows")
    if any(not isinstance(row, list) or len(row) != len(EVIDENCE_ROW_SCHEMA) or
           any(not isinstance(value, str) for value in row) for row in evidence_rows):
        raise ValueError("statement-label evidence row schema mismatch")
    evidence_by_id = {row[0]: dict(zip(EVIDENCE_ROW_SCHEMA, row)) for row in evidence_rows}
    ledger_by_id = {row.get("qId", ""): row for row in ledger}
    if (len(evidence_by_id) != 51 or len(ledger_by_id) != 51 or "" in ledger_by_id or
            set(evidence_by_id) != set(ledger_by_id)):
        raise ValueError("statement-label qId inventory mismatch")
    if set(ledger_by_id) & EXCLUDED_QIDS:
        raise ValueError("blocked R6-028 or Q38 qId is present")
    for q_id, row in ledger_by_id.items():
        official = evidence_by_id[q_id]
        if official["status"] != "confirmed_missing" or row["status"] != "approved_label_only_patch":
            raise ValueError(f"statement-label approval status mismatch: {q_id}")
        if (official["official_source_url"] != row["official_source_url"] or
                official["official_pdf_sha256"] != row["official_pdf_sha256"] or
                official["pdf_page_1based"] != row["pdf_page_1based"] or
                official["expected_label_sequence_ascii"] != encoded_labels(row["expected_label_sequence"])):
            raise ValueError(f"statement-label official source identity mismatch: {q_id}")
        if not official["official_source_url"].startswith("https://www.retio.or.jp/"):
            raise ValueError(f"statement-label source is not fixed RETIO HTTPS: {q_id}")
        if not SHA256_RE.fullmatch(official["official_pdf_sha256"]):
            raise ValueError(f"statement-label official PDF hash is invalid: {q_id}")
        if official["ledger_row_sha256"] != ledger_row_sha256(row, headers):
            raise ValueError(f"statement-label ledger row hash mismatch: {q_id}")


def main() -> None:
    raw = EVIDENCE.read_bytes()
    canonical = canonical_evidence_bytes(raw)
    if hashlib.sha256(canonical).hexdigest() != EVIDENCE_SHA256:
        raise ValueError("statement-label evidence file SHA-256 mismatch")
    if b"@" in canonical:
        raise ValueError("statement-label evidence unexpectedly contains an email-like marker")
    evidence = json.loads(raw.decode("utf-8-sig"))
    headers, ledger = read_ledger()
    validate(evidence, headers, ledger)

    for variant in (
        canonical,
        canonical.replace(b"\n", b"\r\n"),
        canonical.replace(b"\n", b"\r"),
        b"\xef\xbb\xbf" + canonical.replace(b"\n", b"\r\n"),
    ):
        if hashlib.sha256(canonical_evidence_bytes(variant)).hexdigest() != EVIDENCE_SHA256:
            raise ValueError("statement-label evidence checkout normalization mismatch")

    changed_schema = copy.deepcopy(evidence)
    changed_schema["unexpected"] = True
    changed_count = copy.deepcopy(evidence)
    changed_count["rows"].pop()
    changed_hash = copy.deepcopy(evidence)
    changed_hash["rows"][0][-1] = "0" * 64
    changed_label = copy.deepcopy(evidence)
    changed_label["rows"][0][5] = "A,I"
    changed_status = copy.deepcopy(evidence)
    changed_status["rows"][0][1] = "unverified"
    inserted_excluded = copy.deepcopy(evidence)
    inserted_excluded["rows"][0][0] = "R6takken-028"
    changed_ledger = copy.deepcopy(ledger)
    changed_ledger[0]["protected_fields"] += ",unexpected"
    fixtures = [
        (changed_schema, ledger, "schema"), (changed_count, ledger, "count"),
        (changed_hash, ledger, "hash"), (changed_label, ledger, "label"),
        (changed_status, ledger, "status"), (inserted_excluded, ledger, "excluded qId"),
        (evidence, changed_ledger, "protected ledger drift"),
    ]
    for fixture, ledger_fixture, label in fixtures:
        try:
            validate(fixture, headers, ledger_fixture)
        except ValueError:
            pass
        else:
            raise AssertionError(f"fail-closed fixture was accepted: {label}")

    print({
        "ok": True, "ledgerRows": len(ledger), "officialConfirmedMissing": 51,
        "blockedAndQ38Excluded": 3, "checkoutFixtures": 4, "failClosedFixtures": 7,
    })


if __name__ == "__main__":
    main()
