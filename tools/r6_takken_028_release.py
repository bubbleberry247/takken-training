"""Validate and materialize the approved R6takken-028 stem-only release.

The checked-in ledger is content-addressed from independently reviewed official
source evidence. This tool never derives text or an answer from OCR/current data.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "data" / "r6_takken_028_release_ledger.csv"
SOURCE = ROOT / "data" / "takken_all_final.csv"
IMPORT = ROOT / "data" / "takken_questionbank_import.csv"
SPEC = ROOT / "src" / "patchR6Takken028Spec.gs"
WORK = ROOT / "work" / "statement-label-audit-20260821"
WORK_PAYLOAD = WORK / "r6_q28_restoration_full_payload.json"
WORK_LEDGER = WORK / "r6_q28_restoration_release_ledger.csv"
WORK_MANIFEST = WORK / "r6_q28_restoration_source_manifest.json"
WORK_SUMMARY = WORK / "r6_q28_restoration_summary.md"
WORK_BUILDER = WORK / "build_r6_q28_restoration_audit.py"
QID = "R6takken-028"
ROW_COUNT = 600
OFFICIAL_URL = "https://www.retio.or.jp/wp-content/uploads/2025/03/R6_question_answer.pdf"
OFFICIAL_PDF_SHA256 = "82a95815f991567ebc4982b05a15a71f6ec942bd6794c3bafe3bcf9c2e985bae"
OFFICIAL_PAGE = "16"
OFFICIAL_SOURCE_KIND = "RETIO_official_question_pdf"
OFFICIAL_LABEL_SEQUENCE = "ア・イ・ウ"
ALLOWED_FIELDS = {"stem"}
UTF8_BOM = b"\xef\xbb\xbf"
REQUIRED_LEDGER_COLUMNS = {
    "qId", "release_status", "official_source_url", "official_pdf_sha256",
    "pdf_page_1based", "source_kind", "expected_label_sequence",
    "expected_before_source_row_sha256", "expected_before_runtime_row_sha256",
    "field_whitelist", "before_values_json", "replacement_values_json",
    "before_values_sha256", "replacement_values_sha256",
    "expected_after_source_row_sha256", "expected_after_runtime_row_sha256",
    "reviewer", "reviewed_at", "approval_evidence_sha256", "notes",
}


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def canonical_text(value: object) -> str:
    return str("" if value is None else value).replace("\r\n", "\n").replace("\r", "\n")


def canonical_evidence_bytes(raw: bytes) -> bytes:
    """Return the release-evidence byte form used on every OS.

    A single leading UTF-8 BOM is ignored, text must be valid UTF-8, and every
    CRLF or CR line ending is normalized to LF. The returned form never has a
    BOM. This is intentionally separate from Git's checkout representation.
    """
    if raw.startswith(UTF8_BOM):
        raw = raw[len(UTF8_BOM):]
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError("approved work evidence must be valid UTF-8") from exc
    return canonical_text(text).encode("utf-8")


def evidence_sha256_for_paths(paths: list[Path]) -> str:
    entries = []
    for path in paths:
        if not path.is_file():
            raise ValueError(f"approved work evidence is missing: {path.name}")
        canonical_hash = hashlib.sha256(canonical_evidence_bytes(path.read_bytes())).hexdigest()
        entries.append(f"{path.name}:{canonical_hash}")
    return sha256_text("r6-q28-evidence-v1\n" + "\n".join(entries))


def row_sha256(row: dict[str, str], headers: list[str]) -> str:
    payload = "\x1f".join(f"{header}\x1e{canonical_text(row.get(header, ''))}" for header in headers)
    return sha256_text(payload)


def values_sha256(values: dict[str, str], whitelist: list[str]) -> str:
    payload = "\x1f".join(f"{field}\x1e{canonical_text(values[field])}" for field in whitelist)
    return sha256_text(payload)


def read_dataset(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        headers = list(reader.fieldnames or [])
        rows = list(reader)
    if len(rows) != ROW_COUNT:
        raise ValueError(f"{path.name}: expected {ROW_COUNT} rows, got {len(rows)}")
    qids = [row.get("qId", "") for row in rows]
    if len(set(qids)) != ROW_COUNT or any(not qid for qid in qids):
        raise ValueError(f"{path.name}: qId inventory is not 600 unique nonblank values")
    return headers, rows


def find_target(rows: list[dict[str, str]], label: str) -> dict[str, str]:
    found = [row for row in rows if row.get("qId") == QID]
    if len(found) != 1:
        raise ValueError(f"{label}: {QID} must occur exactly once, got {len(found)}")
    return found[0]


def read_ledger() -> dict[str, str]:
    with LEDGER.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        missing = REQUIRED_LEDGER_COLUMNS - set(reader.fieldnames or [])
        if missing:
            raise ValueError("release ledger schema missing: " + ", ".join(sorted(missing)))
        rows = list(reader)
    if len(rows) != 1 or rows[0].get("qId") != QID:
        raise ValueError(f"release ledger must contain exactly one {QID} row")
    return rows[0]


def parse_payload(raw: str, label: str) -> dict[str, str]:
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{label} is not valid JSON: {exc}") from exc
    if not isinstance(payload, dict) or any(not isinstance(k, str) or not isinstance(v, str) for k, v in payload.items()):
        raise ValueError(f"{label} must be a JSON object containing string values")
    return payload


def validate_hash(value: str, label: str, *, required: bool = True) -> None:
    if not value and not required:
        return
    if not re.fullmatch(r"[0-9a-f]{64}", value or ""):
        raise ValueError(f"{label} must be a lowercase SHA-256")


def validate_release() -> dict[str, object]:
    ledger = read_ledger()
    source_headers, source_rows = read_dataset(SOURCE)
    import_headers, import_rows = read_dataset(IMPORT)
    if source_headers != import_headers:
        raise ValueError("canonical and import headers differ")
    source_row = find_target(source_rows, SOURCE.name)
    import_row = find_target(import_rows, IMPORT.name)

    source_hash = row_sha256(source_row, source_headers)
    runtime_hash = row_sha256(import_row, import_headers)
    for name in (
        "expected_before_source_row_sha256", "expected_before_runtime_row_sha256",
    ):
        validate_hash(ledger[name], name)
    if ledger["official_source_url"] != OFFICIAL_URL:
        raise ValueError("official_source_url does not match the fixed RETIO source")
    validate_hash(ledger["official_pdf_sha256"], "official_pdf_sha256")
    if (ledger["official_pdf_sha256"] != OFFICIAL_PDF_SHA256 or
            ledger["pdf_page_1based"] != OFFICIAL_PAGE or
            ledger["source_kind"] != OFFICIAL_SOURCE_KIND or
            ledger["expected_label_sequence"] != OFFICIAL_LABEL_SEQUENCE):
        raise ValueError("official source hash/page/kind/label identity mismatch")

    status = ledger["release_status"].strip().lower()
    if status not in {"blocked", "approved"}:
        raise ValueError("release_status must be blocked or approved")

    payload_columns = (
        "field_whitelist", "before_values_json", "replacement_values_json",
        "before_values_sha256", "replacement_values_sha256",
        "expected_after_source_row_sha256", "expected_after_runtime_row_sha256",
        "reviewer", "reviewed_at", "approval_evidence_sha256",
    )
    if status == "blocked":
        populated = [name for name in payload_columns if ledger[name].strip()]
        if populated:
            raise ValueError("blocked ledger must not contain approval/replacement payload: " + ", ".join(populated))
        if source_hash != ledger["expected_before_source_row_sha256"]:
            raise ValueError("blocked canonical premise hash changed")
        if runtime_hash != ledger["expected_before_runtime_row_sha256"]:
            raise ValueError("blocked import/runtime premise hash changed")
        return {
            "ledger": ledger,
            "headers": source_headers,
            "status": status,
            "whitelist": [],
            "before": {},
            "replacement": {},
            "source_state": "before",
            "runtime_state": "before",
            "source_hash": source_hash,
            "runtime_hash": runtime_hash,
        }

    whitelist = [field.strip() for field in ledger["field_whitelist"].split(",") if field.strip()]
    if not whitelist or len(whitelist) != len(set(whitelist)):
        raise ValueError("approved field_whitelist must be nonblank and unique")
    if whitelist != ["stem"] or set(whitelist) != ALLOWED_FIELDS:
        raise ValueError("approved field_whitelist must be exactly stem")
    before = parse_payload(ledger["before_values_json"], "before_values_json")
    replacement = parse_payload(ledger["replacement_values_json"], "replacement_values_json")
    if set(before) != set(whitelist) or set(replacement) != set(whitelist):
        raise ValueError("payload keys must exactly equal field_whitelist")
    if any(canonical_text(before[field]) == canonical_text(replacement[field]) for field in whitelist):
        raise ValueError("field_whitelist must contain changed fields only")
    for name in (
        "before_values_sha256", "replacement_values_sha256",
        "expected_after_source_row_sha256", "expected_after_runtime_row_sha256",
        "approval_evidence_sha256",
    ):
        validate_hash(ledger[name], name)
    if values_sha256(before, whitelist) != ledger["before_values_sha256"]:
        raise ValueError("before_values_sha256 mismatch")
    if values_sha256(replacement, whitelist) != ledger["replacement_values_sha256"]:
        raise ValueError("replacement_values_sha256 mismatch")
    if not ledger["reviewer"].strip() or not ledger["reviewed_at"].strip():
        raise ValueError("approved ledger requires reviewer and reviewed_at")

    def state(row: dict[str, str], row_hash: str, before_hash: str, after_hash: str, label: str) -> str:
        if row_hash == before_hash:
            for field in whitelist:
                if canonical_text(row[field]) != canonical_text(before[field]):
                    raise ValueError(f"{label}: before payload does not match {field}")
            return "before"
        if row_hash == after_hash:
            for field in whitelist:
                if canonical_text(row[field]) != canonical_text(replacement[field]):
                    raise ValueError(f"{label}: replacement payload does not match {field}")
            return "after"
        raise ValueError(f"{label}: row is neither approved before nor approved after state")

    source_state = state(
        source_row, source_hash, ledger["expected_before_source_row_sha256"],
        ledger["expected_after_source_row_sha256"], "canonical",
    )
    runtime_state = state(
        import_row, runtime_hash, ledger["expected_before_runtime_row_sha256"],
        ledger["expected_after_runtime_row_sha256"], "import",
    )
    if source_state != runtime_state:
        raise ValueError("canonical and import are on different release states")
    return {
        "ledger": ledger,
        "headers": source_headers,
        "status": status,
        "whitelist": whitelist,
        "before": before,
        "replacement": replacement,
        "source_state": source_state,
        "runtime_state": runtime_state,
        "source_hash": source_hash,
        "runtime_hash": runtime_hash,
    }


def work_evidence_sha256() -> str:
    files = [WORK_BUILDER, WORK_LEDGER, WORK_MANIFEST, WORK_PAYLOAD, WORK_SUMMARY]
    return evidence_sha256_for_paths(files)


def approved_ledger_from_work() -> dict[str, str]:
    """Translate the independently approved work-only artifacts into one release row.

    No text or answer is synthesized here. The only replacement value comes from
    the official-source payload, and every preserve field/hash is cross-checked.
    """
    ledger = read_ledger()
    payload = json.loads(WORK_PAYLOAD.read_text(encoding="utf-8"))
    manifest = json.loads(WORK_MANIFEST.read_text(encoding="utf-8"))
    with WORK_LEDGER.open("r", encoding="utf-8-sig", newline="") as handle:
        work_rows = list(csv.DictReader(handle))
    if payload.get("qId") != QID or manifest.get("qId") != QID or len(work_rows) != 18:
        raise ValueError("approved work evidence target/count mismatch")
    if payload.get("status") != "approved_restoration_specification_production_apply_requires_live_hash_preflight":
        raise ValueError("work payload is not an approved restoration specification")
    if (manifest.get("official_pdf_url") != OFFICIAL_URL or
            manifest.get("official_pdf_sha256") != OFFICIAL_PDF_SHA256 or
            str(manifest.get("question_physical_page_1based")) != OFFICIAL_PAGE or
            manifest.get("answer_key") != "B" or str(manifest.get("answer_number")) != "2"):
        raise ValueError("work source manifest identity/answer mismatch")
    if manifest.get("direct_live_row_export") is not False:
        raise ValueError("work source manifest live-state flag is unexpected")

    if any(row.get("qId") != QID or row.get("release_status") != "approved_spec_pending_live_hash_preflight" for row in work_rows):
        raise ValueError("work release ledger status/qId mismatch")
    replace_rows = [row for row in work_rows if row.get("action") == "replace"]
    preserve_rows = [row for row in work_rows if row.get("action") == "preserve"]
    if len(replace_rows) != 1 or replace_rows[0].get("field") != "stem" or len(preserve_rows) != 17:
        raise ValueError("work release ledger must approve stem-only replacement")

    old = payload.get("old") or {}
    proposed = payload.get("proposed") or {}
    official = payload.get("official_structure") or {}
    if not isinstance(old, dict) or not isinstance(proposed, dict):
        raise ValueError("work payload old/proposed records are invalid")
    if set(old) != set(proposed) or [field for field in old if canonical_text(old[field]) != canonical_text(proposed[field])] != ["stem"]:
        raise ValueError("work payload must differ in stem only")
    before_stem = canonical_text(old.get("stem", ""))
    replacement_stem = canonical_text(proposed.get("stem", ""))
    if sha256_text(before_stem) != replace_rows[0].get("old_sha256") or sha256_text(replacement_stem) != replace_rows[0].get("new_sha256"):
        raise ValueError("work payload stem hashes do not match work release ledger")
    if re.findall(r"(?:^|\n)([アイウ])　", replacement_stem) != ["ア", "イ", "ウ"]:
        raise ValueError("approved replacement stem label sequence mismatch")
    if official.get("correct_key") != "B" or str(official.get("correct_number")) != "2":
        raise ValueError("approved work payload answer identity mismatch")

    source_headers, source_rows = read_dataset(SOURCE)
    import_headers, import_rows = read_dataset(IMPORT)
    source_current = find_target(source_rows, SOURCE.name)
    import_current = find_target(import_rows, IMPORT.name)
    for field in ("choiceA", "choiceB", "choiceC", "choiceD", "choiceE", "correct"):
        if source_current[field] != import_current[field] or source_current[field] != old[field] or old[field] != proposed[field]:
            raise ValueError(f"approved preserve field mismatch: {field}")
    if source_current["correct"] != "B":
        raise ValueError("current correct key does not match official B")

    source_before = dict(source_current)
    import_before = dict(import_current)
    source_before["stem"] = before_stem
    import_before["stem"] = before_stem
    source_after = dict(source_before)
    import_after = dict(import_before)
    source_after["stem"] = replacement_stem
    import_after["stem"] = replacement_stem
    expected_before_source = row_sha256(source_before, source_headers)
    expected_before_runtime = row_sha256(import_before, import_headers)
    if (expected_before_source != ledger["expected_before_source_row_sha256"] or
            expected_before_runtime != ledger["expected_before_runtime_row_sha256"]):
        raise ValueError("work payload does not reconstruct the fixed before full-row hashes")
    source_current_hash = row_sha256(source_current, source_headers)
    import_current_hash = row_sha256(import_current, import_headers)
    expected_after_source = row_sha256(source_after, source_headers)
    expected_after_runtime = row_sha256(import_after, import_headers)
    if source_current_hash not in {expected_before_source, expected_after_source} or import_current_hash not in {expected_before_runtime, expected_after_runtime}:
        raise ValueError("current canonical/import row has drifted outside approved before/after states")
    if (source_current_hash == expected_before_source) != (import_current_hash == expected_before_runtime):
        raise ValueError("canonical/import are on different states before approval import")

    field_whitelist = ["stem"]
    before_values = {"stem": before_stem}
    replacement_values = {"stem": replacement_stem}
    approved = dict(ledger)
    approved.update({
        "release_status": "approved",
        "field_whitelist": "stem",
        "before_values_json": json.dumps(before_values, ensure_ascii=False, separators=(",", ":")),
        "replacement_values_json": json.dumps(replacement_values, ensure_ascii=False, separators=(",", ":")),
        "before_values_sha256": values_sha256(before_values, field_whitelist),
        "replacement_values_sha256": values_sha256(replacement_values, field_whitelist),
        "expected_after_source_row_sha256": expected_after_source,
        "expected_after_runtime_row_sha256": expected_after_runtime,
        "reviewer": "independent_official_source_audit",
        "reviewed_at": "2026-08-22",
        "approval_evidence_sha256": work_evidence_sha256(),
        "notes": "Approved stem-only restoration. Official answer B and all non-stem fields preserved. Production apply still requires direct live full-row hash preflight.",
    })
    return approved


def write_approved_ledger_from_work() -> None:
    approved = approved_ledger_from_work()
    with LEDGER.open("r", encoding="utf-8-sig", newline="") as handle:
        headers = list(csv.DictReader(handle).fieldnames or [])
    with LEDGER.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers, lineterminator="\n")
        writer.writeheader()
        writer.writerow(approved)


def generated_spec(validated: dict[str, object]) -> str:
    ledger = validated["ledger"]
    assert isinstance(ledger, dict)
    spec = {
        "qId": QID,
        "releaseStatus": validated["status"],
        "officialSourceSha256": ledger["official_pdf_sha256"],
        "officialSourcePage": int(ledger["pdf_page_1based"]),
        "sourceKind": ledger["source_kind"],
        "expectedLabelSequence": ledger["expected_label_sequence"],
        "expectedBeforeRuntimeRowSha256": ledger["expected_before_runtime_row_sha256"],
        "expectedAfterRuntimeRowSha256": ledger["expected_after_runtime_row_sha256"],
        "fieldWhitelist": validated["whitelist"],
        "beforeValues": validated["before"],
        "replacementValues": validated["replacement"],
        "beforeValuesSha256": ledger["before_values_sha256"],
        "replacementValuesSha256": ledger["replacement_values_sha256"],
        "approvalEvidenceSha256": ledger["approval_evidence_sha256"],
        "reviewedAt": ledger["reviewed_at"],
    }
    body = json.dumps(spec, ensure_ascii=False, indent=2, sort_keys=True)
    return (
        "// GENERATED by tools/r6_takken_028_release.py. Do not hand-edit.\n"
        "// A blocked spec contains no problem text, choices, or answer payload.\n"
        f"var TAKKEN_R6_028_RELEASE_SPEC_ = {body};\n"
    )


def write_source(validated: dict[str, object]) -> None:
    if validated["status"] != "approved":
        raise ValueError("source sync is blocked until release_status=approved")
    if validated["source_state"] == "after" and validated["runtime_state"] == "after":
        return
    if validated["source_state"] != "before" or validated["runtime_state"] != "before":
        raise ValueError("source sync requires canonical and import in the approved before state")
    headers, rows = read_dataset(SOURCE)
    target = find_target(rows, SOURCE.name)
    for field in validated["whitelist"]:
        target[field] = validated["replacement"][field]
    expected = validated["ledger"]["expected_after_source_row_sha256"]
    if row_sha256(target, headers) != expected:
        raise ValueError("post-sync canonical full-row hash mismatch; source not written")
    temp = SOURCE.with_suffix(".csv.r6-028.tmp")
    with temp.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    temp.replace(SOURCE)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="validate ledger/data and check generated spec")
    parser.add_argument("--generate", action="store_true", help="write the generated GAS release spec")
    parser.add_argument("--apply-source", action="store_true", help="apply an approved payload to canonical CSV only")
    parser.add_argument("--approve-from-work-ledger", action="store_true", help="materialize approved stem-only release row from independently audited work artifacts")
    args = parser.parse_args()
    if sum(bool(value) for value in (args.check, args.generate, args.apply_source, args.approve_from_work_ledger)) > 1:
        parser.error("choose one action")
    if args.approve_from_work_ledger:
        write_approved_ledger_from_work()
    validated = validate_release()
    expected_spec = generated_spec(validated)
    if args.apply_source:
        write_source(validated)
    elif args.generate:
        SPEC.write_text(expected_spec, encoding="utf-8", newline="\n")
    elif args.check:
        if not SPEC.exists() or SPEC.read_text(encoding="utf-8") != expected_spec:
            raise ValueError("generated patchR6Takken028Spec.gs is stale; run --generate")
    print(json.dumps({
        "ok": True,
        "qIdCount": 1,
        "datasetRows": ROW_COUNT,
        "nonTargetCount": ROW_COUNT - 1,
        "releaseStatus": validated["status"],
        "fieldCount": len(validated["whitelist"]),
        "sourceState": validated["source_state"],
        "runtimeState": validated["runtime_state"],
        "contentIncluded": bool(validated["whitelist"]),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2)
