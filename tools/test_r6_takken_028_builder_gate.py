import csv
import importlib.util
import json
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("takken_builder", ROOT / "tools" / "build_takken_import_csv.py")
builder = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(builder)


def read_csv(path):
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def write_ledger(path, headers, row):
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers, lineterminator="\n")
        writer.writeheader()
        writer.writerow(row)


source_headers, source_rows = read_csv(ROOT / "data" / "takken_all_final.csv")
import_headers, import_rows = read_csv(ROOT / "data" / "takken_questionbank_import.csv")
assert source_headers == import_headers == builder.HEADERS
builder.validate_r6_028_release_state(source_rows, "canonical")
builder.validate_r6_028_release_state(import_rows, "runtime")

ledger_headers, ledger_rows = read_csv(ROOT / "data" / "r6_takken_028_release_ledger.csv")
base = ledger_rows[0]
with tempfile.TemporaryDirectory(prefix="r6-builder-gate-") as tmp_name:
    temp_ledger = Path(tmp_name) / "ledger.csv"
    original = builder.R6_028_RELEASE_LEDGER
    builder.R6_028_RELEASE_LEDGER = temp_ledger
    try:
        protected = dict(base)
        before = {"status": "published"}
        replacement = {"status": "hidden"}
        protected.update({
            "field_whitelist": "status",
            "before_values_json": json.dumps(before),
            "replacement_values_json": json.dumps(replacement),
            "before_values_sha256": builder.release_values_sha256(before, ["status"]),
            "replacement_values_sha256": builder.release_values_sha256(replacement, ["status"]),
        })
        write_ledger(temp_ledger, ledger_headers, protected)
        try:
            builder.validate_r6_028_release_state(source_rows, "canonical")
            raise AssertionError("generator accepted protected status field")
        except ValueError as exc:
            assert "exactly stem" in str(exc)

        formerly_allowed = dict(base)
        formerly_allowed.update({
            "field_whitelist": "choiceA",
            "before_values_json": json.dumps({"choiceA": "before"}),
            "replacement_values_json": json.dumps({"choiceA": "after"}),
            "before_values_sha256": builder.release_values_sha256({"choiceA": "before"}, ["choiceA"]),
            "replacement_values_sha256": builder.release_values_sha256({"choiceA": "after"}, ["choiceA"]),
        })
        write_ledger(temp_ledger, ledger_headers, formerly_allowed)
        try:
            builder.validate_r6_028_release_state(source_rows, "canonical")
            raise AssertionError("generator accepted choiceA-only release")
        except ValueError as exc:
            assert "exactly stem" in str(exc)

        bad_hash = dict(base)
        bad_hash["replacement_values_sha256"] = "0" * 64
        write_ledger(temp_ledger, ledger_headers, bad_hash)
        try:
            builder.validate_r6_028_release_state(source_rows, "canonical")
            raise AssertionError("generator accepted a bad payload hash")
        except ValueError as exc:
            assert "replacement_values_sha256 mismatch" in str(exc) or "payload hash mismatch" in str(exc)

        bad_approval_hash = dict(base)
        bad_approval_hash["approval_evidence_sha256"] = "0" * 64
        write_ledger(temp_ledger, ledger_headers, bad_approval_hash)
        try:
            builder.validate_r6_028_release_state(source_rows, "canonical")
            raise AssertionError("generator accepted changed composite approval evidence")
        except ValueError as exc:
            assert "composite approval evidence" in str(exc)

        bad_live_override = dict(base)
        bad_live_override["live_baseline_overrides_json"] = json.dumps({"explainLong": "unexpected"})
        write_ledger(temp_ledger, ledger_headers, bad_live_override)
        try:
            builder.validate_r6_028_release_state(source_rows, "canonical")
            raise AssertionError("generator accepted changed live protected baseline")
        except ValueError as exc:
            assert "live baseline" in str(exc) or "preserve explainLong" in str(exc)

        bad_receipt_hash = dict(base)
        bad_receipt_hash["live_diagnostic_receipt_sha256"] = "0" * 64
        write_ledger(temp_ledger, ledger_headers, bad_receipt_hash)
        try:
            builder.validate_r6_028_release_state(source_rows, "canonical")
            raise AssertionError("generator accepted changed live receipt identity")
        except ValueError as exc:
            assert "live diagnostic receipt" in str(exc)

        no_reviewer = dict(base)
        no_reviewer["reviewer"] = ""
        write_ledger(temp_ledger, ledger_headers, no_reviewer)
        try:
            builder.validate_r6_028_release_state(source_rows, "canonical")
            raise AssertionError("generator accepted missing reviewer")
        except ValueError as exc:
            assert "reviewer" in str(exc)

        blocked_residue = dict(base)
        blocked_residue["release_status"] = "blocked"
        blocked_residue["expected_before_source_row_sha256"] = builder.full_row_sha256(next(row for row in source_rows if row["qId"] == builder.R6_028_QID))
        blocked_residue["expected_before_runtime_row_sha256"] = builder.full_row_sha256(next(row for row in import_rows if row["qId"] == builder.R6_028_QID))
        write_ledger(temp_ledger, ledger_headers, blocked_residue)
        try:
            builder.validate_r6_028_release_state(source_rows, "canonical")
            raise AssertionError("generator accepted blocked approval residue")
        except ValueError as exc:
            assert "blocked" in str(exc) and "payload" in str(exc)
    finally:
        builder.R6_028_RELEASE_LEDGER = original

print(json.dumps({
    "ok": True,
    "tests": 12,
    "standaloneGeneratorGate": True,
    "rejected": ["protected-field", "choiceA-field", "bad-payload-hash", "approval-evidence", "live-baseline", "live-receipt", "missing-reviewer", "blocked-residue"],
}))
