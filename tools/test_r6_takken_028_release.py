import csv
import datetime as dt
import importlib.util
import json
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools" / "r6_takken_028_release.py"
SPEC = importlib.util.spec_from_file_location("r6_release", MODULE_PATH)
release = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(release)


def read_csv(path):
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def write_csv(path, headers, rows):
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


# Checked-in state is independently approved, synchronized, and stem-only.
checked_in = release.validate_release()
assert checked_in["status"] == "approved"
assert checked_in["source_state"] == "after"
assert checked_in["runtime_state"] == "after"
assert checked_in["whitelist"] == ["stem"]
generated_checked_in = release.generated_spec(checked_in)
assert '"releaseStatus": "approved"' in generated_checked_in
assert (ROOT / "src" / "patchR6Takken028Spec.gs").read_text(encoding="utf-8") == generated_checked_in
assert release.approved_ledger_from_work() == checked_in["ledger"]
source_bytes_before = release.SOURCE.read_bytes()
release.write_source(checked_in)
assert release.SOURCE.read_bytes() == source_bytes_before

# Header-aware date canonicalization matches the live Asia/Tokyo date cell and
# is stable across the UTC midnight boundary. Strings remain exact strings.
assert release.canonical_cell("2026-04-10", "updatedAt") == "2026-04-10"
assert release.canonical_cell(dt.datetime(2026, 4, 9, 15, 0, tzinfo=dt.timezone.utc), "updatedAt") == "2026-04-10"
assert release.canonical_cell(dt.datetime(2026, 4, 9, 14, 59, 59, tzinfo=dt.timezone.utc), "updatedAt") == "2026-04-09"
assert release.canonical_cell(dt.datetime(2026, 4, 10, 0, 0, tzinfo=release.JST), "updatedAt") == "2026-04-10"
assert release.canonical_cell(dt.datetime(2026, 4, 9, 15, 0, tzinfo=dt.timezone.utc), "other") == "2026-04-10"
assert release.normalize_headers([" qId ", "updatedAt "]) == ["qId", "updatedAt"]
for bad_headers in (["qId", " qId "], ["qId", " "]):
    try:
        release.normalize_headers(list(bad_headers))
        raise AssertionError("invalid normalized headers were accepted")
    except ValueError as exc:
        assert "unique nonblank" in str(exc)
try:
    release.canonical_cell(dt.datetime(2026, 4, 10), "updatedAt")
    raise AssertionError("naive datetime was accepted")
except ValueError as exc:
    assert "naive datetime" in str(exc)

# The exact read-only diagnostic receipt is approval evidence; missing or
# byte-modified evidence fails closed.
assert release.validate_live_diagnostic_receipt()["databaseChanged"] is False
with tempfile.TemporaryDirectory(prefix="r6-028-live-receipt-") as receipt_tmp_name:
    original_receipt_path = release.LIVE_DIAGNOSTIC_RECEIPT
    try:
        missing_path = Path(receipt_tmp_name) / "missing.json"
        release.LIVE_DIAGNOSTIC_RECEIPT = missing_path
        try:
            release.validate_live_diagnostic_receipt()
            raise AssertionError("missing live receipt was accepted")
        except ValueError as exc:
            assert "missing" in str(exc)
        crlf_path = Path(receipt_tmp_name) / ("crlf-" + original_receipt_path.name)
        canonical_receipt = release.canonical_evidence_bytes(original_receipt_path.read_bytes())
        crlf_path.write_bytes(canonical_receipt.replace(b"\n", b"\r\n"))
        release.LIVE_DIAGNOSTIC_RECEIPT = crlf_path
        try:
            release.validate_live_diagnostic_receipt()
            raise AssertionError("CRLF-modified raw receipt was accepted")
        except ValueError as exc:
            assert "SHA-256 mismatch" in str(exc)
        bom_path = Path(receipt_tmp_name) / ("bom-" + original_receipt_path.name)
        bom_path.write_bytes(release.UTF8_BOM + original_receipt_path.read_bytes())
        release.LIVE_DIAGNOSTIC_RECEIPT = bom_path
        try:
            release.validate_live_diagnostic_receipt()
            raise AssertionError("BOM-prefixed raw receipt was accepted")
        except ValueError as exc:
            assert "SHA-256 mismatch" in str(exc)
        tampered_path = Path(receipt_tmp_name) / original_receipt_path.name
        tampered_path.write_bytes(original_receipt_path.read_bytes() + b"\n")
        release.LIVE_DIAGNOSTIC_RECEIPT = tampered_path
        try:
            release.validate_live_diagnostic_receipt()
            raise AssertionError("tampered live receipt was accepted")
        except ValueError as exc:
            assert "SHA-256 mismatch" in str(exc)
    finally:
        release.LIVE_DIAGNOSTIC_RECEIPT = original_receipt_path

# Each data plane changes only stem from its own approved before state to its
# approved after state. Cross-plane generator enrichment is a separate,
# pre-existing seven-column normalization contract.
source_headers_now, source_rows_now = read_csv(release.SOURCE)
import_headers_now, import_rows_now = read_csv(release.IMPORT)
source_after_now = next(row for row in source_rows_now if row["qId"] == release.QID)
import_after_now = next(row for row in import_rows_now if row["qId"] == release.QID)
before_stem = json.loads(checked_in["ledger"]["before_values_json"])["stem"]
for plane_name, after_row in (("canonical", source_after_now), ("import", import_after_now)):
    before_row = dict(after_row)
    before_row["stem"] = before_stem
    changed = [header for header in source_headers_now if before_row[header] != after_row[header]]
    assert changed == ["stem"], (plane_name, changed)
expected_cross_plane_enrichment = {
    "segmentId", "type", "difficulty", "tag2", "revisionFlag", "variantGroupId", "updatedAt",
}
actual_cross_plane_differences = {
    header for header in source_headers_now if source_after_now[header] != import_after_now[header]
}
assert actual_cross_plane_differences == expected_cross_plane_enrichment

# Evidence identity is based on canonical UTF-8 text, not checkout bytes.
# A leading UTF-8 BOM is ignored and CRLF/CR are normalized to LF.
current_evidence_hash = release.work_evidence_sha256()
evidence_paths = [
    release.OFFICIAL_APPROVAL_EVIDENCE,
]
canonical_evidence = {
    path.name: release.canonical_evidence_bytes(path.read_bytes())
    for path in evidence_paths
}


def mixed_line_endings(raw):
    parts = raw.split(b"\n")
    output = bytearray(parts[0])
    # Alternate LF/CRLF. Bare CR is covered by the all-CR fixture; mixing a
    # bare CR immediately before an LF would be indistinguishable from CRLF.
    separators = (b"\n", b"\r\n")
    for index, part in enumerate(parts[1:]):
        output.extend(separators[(index + 1) % len(separators)])
        output.extend(part)
    return bytes(output)


with tempfile.TemporaryDirectory(prefix="r6-028-evidence-canonical-") as evidence_tmp_name:
    evidence_root = Path(evidence_tmp_name)
    variants = {
        "all-lf": lambda raw, _index: raw,
        "all-crlf": lambda raw, _index: raw.replace(b"\n", b"\r\n"),
        "all-cr": lambda raw, _index: raw.replace(b"\n", b"\r"),
        "mixed": lambda raw, _index: mixed_line_endings(raw),
        "bom-all": lambda raw, _index: release.UTF8_BOM + raw,
        "bom-mixed": lambda raw, index: (release.UTF8_BOM if index % 2 else b"") + mixed_line_endings(raw),
    }
    for variant_name, transform in variants.items():
        variant_dir = evidence_root / variant_name
        variant_dir.mkdir()
        variant_paths = []
        for index, path in enumerate(evidence_paths):
            variant_path = variant_dir / path.name
            variant_bytes = transform(canonical_evidence[path.name], index)
            assert release.canonical_evidence_bytes(variant_bytes) == canonical_evidence[path.name], (variant_name, path.name)
            variant_path.write_bytes(variant_bytes)
            variant_paths.append(variant_path)
        assert release.evidence_sha256_for_paths(variant_paths) == current_evidence_hash, variant_name

try:
    release.canonical_evidence_bytes(b"\xff")
    raise AssertionError("invalid UTF-8 evidence was accepted")
except ValueError as exc:
    assert "valid UTF-8" in str(exc)

with tempfile.TemporaryDirectory(prefix="r6-028-release-test-") as tmp_name:
    tmp = Path(tmp_name)
    source_path = tmp / "source.csv"
    import_path = tmp / "import.csv"
    ledger_path = tmp / "ledger.csv"
    spec_path = tmp / "spec.gs"
    source_headers, source_rows = read_csv(ROOT / "data" / "takken_all_final.csv")
    import_headers, import_rows = read_csv(ROOT / "data" / "takken_questionbank_import.csv")
    source_target = next(row for row in source_rows if row["qId"] == release.QID)
    import_target = next(row for row in import_rows if row["qId"] == release.QID)
    ledger_headers, ledger_rows = read_csv(ROOT / "data" / "r6_takken_028_release_ledger.csv")
    approved_row = dict(ledger_rows[0])
    whitelist = ["stem"]
    before = json.loads(approved_row["before_values_json"])
    replacement = json.loads(approved_row["replacement_values_json"])
    after_source = dict(source_target)
    after_import = dict(import_target)
    source_target.update(before)
    import_target.update(before)
    write_csv(source_path, source_headers, source_rows)
    write_csv(import_path, import_headers, import_rows)

    blocked_row = dict(approved_row)
    blocked_row.update({
        "release_status": "blocked",
        "field_whitelist": "",
        "before_values_json": "",
        "replacement_values_json": "",
        "before_values_sha256": "",
        "replacement_values_sha256": "",
        "expected_after_source_row_sha256": "",
        "expected_after_runtime_row_sha256": "",
        "reviewer": "",
        "reviewed_at": "",
        "approval_evidence_sha256": "",
    })
    for column in release.LIVE_LEDGER_COLUMNS:
        blocked_row[column] = ""
    write_csv(ledger_path, ledger_headers, [blocked_row])

    original_paths = release.LEDGER, release.SOURCE, release.IMPORT, release.SPEC
    release.LEDGER, release.SOURCE, release.IMPORT, release.SPEC = ledger_path, source_path, import_path, spec_path
    try:
        blocked = release.validate_release()
        assert blocked["status"] == "blocked"
        assert blocked["source_state"] == blocked["runtime_state"] == "before"
        assert blocked["whitelist"] == []
        generated_blocked = release.generated_spec(blocked)
        assert '"releaseStatus": "blocked"' in generated_blocked
        assert "TEST-APPROVED" not in generated_blocked

        write_csv(ledger_path, ledger_headers, [approved_row])
        approved = release.validate_release()
        assert approved["status"] == "approved"
        assert approved["source_state"] == approved["runtime_state"] == "before"
        assert approved["whitelist"] == whitelist
        generated = release.generated_spec(approved)
        assert '"releaseStatus": "approved"' in generated
        assert release.OFFICIAL_REPLACEMENT_STEM_SHA256 == release.sha256_text(replacement["stem"])

        # Canonical synchronization is explicit and content-addressed.
        release.write_source(approved)
        synced_headers, synced_rows = read_csv(source_path)
        synced_target = next(row for row in synced_rows if row["qId"] == release.QID)
        assert release.row_sha256(synced_target, synced_headers) == approved_row["expected_after_source_row_sha256"]
        for field in whitelist:
            assert synced_target[field] == replacement[field]
        for field in source_headers:
            if field not in whitelist:
                assert synced_target[field] == source_target[field]

        # Simulate the deterministic import generator output for the target;
        # validation must then accept both files only in the approved after state.
        import_target.update(replacement)
        write_csv(import_path, import_headers, import_rows)
        approved_after = release.validate_release()
        assert approved_after["source_state"] == approved_after["runtime_state"] == "after"

        # A protected-field whitelist and a stale hash are independent blockers.
        bad_protected = dict(approved_row)
        bad_protected["field_whitelist"] = "stem,status"
        bad_protected["before_values_json"] = json.dumps({"stem": before["stem"], "status": "published"})
        bad_protected["replacement_values_json"] = json.dumps({"stem": replacement["stem"], "status": "hidden"})
        write_csv(ledger_path, ledger_headers, [bad_protected])
        try:
            release.validate_release()
            raise AssertionError("protected field was accepted")
        except ValueError as exc:
            assert "exactly stem" in str(exc)

        formerly_allowed = dict(approved_row)
        formerly_allowed["field_whitelist"] = "choiceA"
        formerly_allowed["before_values_json"] = json.dumps({"choiceA": source_target["choiceA"]})
        formerly_allowed["replacement_values_json"] = json.dumps({"choiceA": "TEST-CHOICE"})
        write_csv(ledger_path, ledger_headers, [formerly_allowed])
        try:
            release.validate_release()
            raise AssertionError("choiceA-only release was accepted")
        except ValueError as exc:
            assert "exactly stem" in str(exc)

        stale = dict(approved_row)
        stale["expected_before_source_row_sha256"] = "0" * 64
        source_target.update(before)
        import_target.update(before)
        write_csv(source_path, source_headers, source_rows)
        write_csv(import_path, import_headers, import_rows)
        write_csv(ledger_path, ledger_headers, [stale])
        try:
            release.validate_release()
            raise AssertionError("stale full-row hash was accepted")
        except ValueError as exc:
            assert "plane hash identity mismatch" in str(exc)

        duplicate_rows = source_rows + [dict(source_target)]
        write_csv(source_path, source_headers, duplicate_rows)
        write_csv(ledger_path, ledger_headers, [approved_row])
        try:
            release.validate_release()
            raise AssertionError("duplicate/601-row dataset was accepted")
        except ValueError as exc:
            assert "expected 600 rows" in str(exc)
    finally:
        release.LEDGER, release.SOURCE, release.IMPORT, release.SPEC = original_paths

print(json.dumps({
    "ok": True,
    "tests": 58,
    "checkedInStatus": checked_in["status"],
    "checkedInPayloadFields": len(checked_in["whitelist"]),
    "approvedFixtureFields": 1,
    "evidenceCheckoutFixtures": 6,
    "liveBaseline": "receipt-bound; explainLong blank; updatedAt date-only",
    "sourceSync": "before-to-after full-row hash verified",
}))
