import csv
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

# Evidence identity is based on canonical UTF-8 text, not checkout bytes.
# A leading UTF-8 BOM is ignored and CRLF/CR are normalized to LF.
current_evidence_hash = release.work_evidence_sha256()
evidence_paths = [
    release.WORK_BUILDER, release.WORK_LEDGER, release.WORK_MANIFEST,
    release.WORK_PAYLOAD, release.WORK_SUMMARY,
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
    write_csv(source_path, source_headers, source_rows)
    write_csv(import_path, import_headers, import_rows)

    source_target = next(row for row in source_rows if row["qId"] == release.QID)
    import_target = next(row for row in import_rows if row["qId"] == release.QID)
    whitelist = ["stem"]
    before = {field: source_target[field] for field in whitelist}
    assert before == {field: import_target[field] for field in whitelist}
    replacement = {"stem": before["stem"] + "\n\nTEST-APPROVED-STATEMENTS"}
    after_source = dict(source_target)
    after_import = dict(import_target)
    after_source.update(replacement)
    after_import.update(replacement)

    ledger_headers, ledger_rows = read_csv(ROOT / "data" / "r6_takken_028_release_ledger.csv")
    blocked_row = dict(ledger_rows[0])
    blocked_row.update({
        "release_status": "blocked",
        "expected_before_source_row_sha256": release.row_sha256(source_target, source_headers),
        "expected_before_runtime_row_sha256": release.row_sha256(import_target, import_headers),
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
    write_csv(ledger_path, ledger_headers, [blocked_row])

    approved_row = dict(ledger_rows[0])
    approved_row.update({
        "release_status": "approved",
        "expected_before_source_row_sha256": release.row_sha256(source_target, source_headers),
        "expected_before_runtime_row_sha256": release.row_sha256(import_target, import_headers),
        "field_whitelist": ",".join(whitelist),
        "before_values_json": json.dumps(before, ensure_ascii=False, separators=(",", ":")),
        "replacement_values_json": json.dumps(replacement, ensure_ascii=False, separators=(",", ":")),
        "before_values_sha256": release.values_sha256(before, whitelist),
        "replacement_values_sha256": release.values_sha256(replacement, whitelist),
        "expected_after_source_row_sha256": release.row_sha256(after_source, source_headers),
        "expected_after_runtime_row_sha256": release.row_sha256(after_import, import_headers),
        "reviewer": "TEST-REVIEWER",
        "reviewed_at": "2099-01-01T00:00:00+09:00",
        "approval_evidence_sha256": "c" * 64,
    })
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
        assert "TEST-APPROVED-STATEMENTS" in generated

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
        write_csv(source_path, source_headers, source_rows)
        write_csv(import_path, import_headers, import_rows)
        write_csv(ledger_path, ledger_headers, [stale])
        try:
            release.validate_release()
            raise AssertionError("stale full-row hash was accepted")
        except ValueError as exc:
            assert "neither approved before nor approved after" in str(exc)

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
    "tests": 40,
    "checkedInStatus": checked_in["status"],
    "checkedInPayloadFields": len(checked_in["whitelist"]),
    "approvedFixtureFields": 1,
    "evidenceCheckoutFixtures": 6,
    "sourceSync": "before-to-after full-row hash verified",
}))
