"""Validate and materialize the approved R6takken-028 stem-only release.

The checked-in ledger is content-addressed from independently reviewed official
source evidence. This tool never derives text or an answer from OCR/current data.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
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
OFFICIAL_APPROVAL_EVIDENCE = ROOT / "data" / "release-evidence" / "r6_q28_official_approval.json"
LIVE_DIAGNOSTIC_RECEIPT = ROOT / "data" / "release-evidence" / "r6_q28_live_hash_diagnostic.json"
LIVE_DIAGNOSTIC_RECEIPT_SHA256 = "b73cffb1a1e5cf43fc5894edb5107c20d5fbc9bd06a39bd280425d344c810925"
LIVE_LEGACY_ROW_SHA256 = "3dc8549a6d8c901e150da72153af4d62293915d241ebfa30286812462ec657c5"
LIVE_BASELINE_OVERRIDES = {"explainLong": ""}
LIVE_DATE_ONLY_FIELDS = {"updatedAt"}
JST = dt.timezone(dt.timedelta(hours=9))
QID = "R6takken-028"
ROW_COUNT = 600
OFFICIAL_URL = "https://www.retio.or.jp/wp-content/uploads/2025/03/R6_question_answer.pdf"
OFFICIAL_PDF_SHA256 = "82a95815f991567ebc4982b05a15a71f6ec942bd6794c3bafe3bcf9c2e985bae"
OFFICIAL_PAGE = "16"
OFFICIAL_SOURCE_KIND = "RETIO_official_question_pdf"
OFFICIAL_LABEL_SEQUENCE = "ア・イ・ウ"
OFFICIAL_BEFORE_STEM_SHA256 = "b60adafe1fbaf4d3d0e5056698486f62b76698fcd06baadf22f1c6fec11a331c"
OFFICIAL_REPLACEMENT_STEM_SHA256 = "9f9907be1958fc9c649703194535907f5aea38f46cfc436766dc5c7dba470f76"
SOURCE_BEFORE_ROW_SHA256 = "40d1a773246688d0e112fc43f0a0f044a54510608ada290a55d405a99a6e347b"
SOURCE_AFTER_ROW_SHA256 = "63904f97af8af28e9d10bf191dd1e9afe0610e07078ba9e9d0eb40f5dce6c164"
IMPORT_BEFORE_ROW_SHA256 = "5531d591e1f07b2bc5b60c1e5f31b46e9723fd781ac2a31d11d12249d82f3919"
IMPORT_AFTER_ROW_SHA256 = "d60ef8583bbd59b9212e128c601367734d939804f3ae21bb5f3050453168eed9"
PRIOR_WORK_EVIDENCE_SHA256 = "91ce890fd039bbe69b631daaf667c4f0f363c1a858eeca7b17eca589a6b54757"
ALLOWED_FIELDS = {"stem"}
UTF8_BOM = b"\xef\xbb\xbf"
LIVE_LEDGER_COLUMNS = (
    "expected_before_live_runtime_row_sha256", "expected_after_live_runtime_row_sha256",
    "live_baseline_overrides_json", "live_date_only_fields",
    "official_work_evidence_sha256", "live_diagnostic_receipt_sha256",
)
REQUIRED_LEDGER_COLUMNS = {
    "qId", "release_status", "official_source_url", "official_pdf_sha256",
    "pdf_page_1based", "source_kind", "expected_label_sequence",
    "expected_before_source_row_sha256", "expected_before_runtime_row_sha256",
    "field_whitelist", "before_values_json", "replacement_values_json",
    "before_values_sha256", "replacement_values_sha256",
    "expected_after_source_row_sha256", "expected_after_runtime_row_sha256",
    *LIVE_LEDGER_COLUMNS,
    "reviewer", "reviewed_at", "approval_evidence_sha256", "notes",
}


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def canonical_text(value: object) -> str:
    return str("" if value is None else value).replace("\r\n", "\n").replace("\r", "\n")


def canonical_cell(value: object, header: str) -> str:
    """Mirror the GAS runtime cell canonicalizer, including date-only fields."""
    if isinstance(value, dt.datetime):
        if value.tzinfo is None:
            raise ValueError(f"naive datetime is not allowed for {header}")
        localized = value.astimezone(JST)
        if header in LIVE_DATE_ONLY_FIELDS:
            return localized.strftime("%Y-%m-%d")
        has_time = any((localized.hour, localized.minute, localized.second, localized.microsecond))
        return localized.strftime("%Y-%m-%d %H:%M:%S" if has_time else "%Y-%m-%d")
    if isinstance(value, dt.date):
        return value.isoformat()
    return canonical_text(value)


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


def row_sha256(row: dict[str, object], headers: list[str]) -> str:
    payload = "\x1f".join(f"{header}\x1e{canonical_cell(row.get(header, ''), header)}" for header in headers)
    return sha256_text(payload)


def values_sha256(values: dict[str, str], whitelist: list[str]) -> str:
    payload = "\x1f".join(f"{field}\x1e{canonical_text(values[field])}" for field in whitelist)
    return sha256_text(payload)


def normalize_headers(raw_headers: list[object]) -> list[str]:
    """Mirror GAS normalizeHeader_: BOM is decoded away and every cell trims."""
    headers = [canonical_text(value).strip() for value in raw_headers]
    if any(not header for header in headers) or len(headers) != len(set(headers)):
        raise ValueError("dataset headers must be unique nonblank normalized names")
    return headers


def read_dataset(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        raw_headers = list(reader.fieldnames or [])
        headers = normalize_headers(raw_headers)
        raw_rows = list(reader)
    if any(None in row for row in raw_rows):
        raise ValueError(f"{path.name}: row wider than normalized header")
    rows = [
        {header: row.get(raw_header, "") for raw_header, header in zip(raw_headers, headers)}
        for row in raw_rows
    ]
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


def read_ledger(*, allow_missing_live_columns: bool = False) -> dict[str, str]:
    with LEDGER.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        missing = REQUIRED_LEDGER_COLUMNS - set(reader.fieldnames or [])
        if missing and not allow_missing_live_columns:
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
        "expected_before_live_runtime_row_sha256", "expected_after_live_runtime_row_sha256",
        "live_baseline_overrides_json", "live_date_only_fields",
        "official_work_evidence_sha256", "live_diagnostic_receipt_sha256",
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
        "expected_before_live_runtime_row_sha256", "expected_after_live_runtime_row_sha256",
        "official_work_evidence_sha256", "live_diagnostic_receipt_sha256",
        "approval_evidence_sha256",
    ):
        validate_hash(ledger[name], name)
    if values_sha256(before, whitelist) != ledger["before_values_sha256"]:
        raise ValueError("before_values_sha256 mismatch")
    if values_sha256(replacement, whitelist) != ledger["replacement_values_sha256"]:
        raise ValueError("replacement_values_sha256 mismatch")
    if not ledger["reviewer"].strip() or not ledger["reviewed_at"].strip():
        raise ValueError("approved ledger requires reviewer and reviewed_at")
    live_overrides = parse_payload(ledger["live_baseline_overrides_json"], "live_baseline_overrides_json")
    if live_overrides != LIVE_BASELINE_OVERRIDES:
        raise ValueError("approved live baseline overrides must preserve explainLong as blank")
    if ledger["live_date_only_fields"] != "updatedAt":
        raise ValueError("approved live date-only contract must be exactly updatedAt")
    fixed_plane_hashes = {
        "expected_before_source_row_sha256": SOURCE_BEFORE_ROW_SHA256,
        "expected_after_source_row_sha256": SOURCE_AFTER_ROW_SHA256,
        "expected_before_runtime_row_sha256": IMPORT_BEFORE_ROW_SHA256,
        "expected_after_runtime_row_sha256": IMPORT_AFTER_ROW_SHA256,
    }
    if any(ledger[name] != value for name, value in fixed_plane_hashes.items()):
        raise ValueError("approved source/import plane hash identity mismatch")
    validate_live_diagnostic_receipt()
    if ledger["official_work_evidence_sha256"] != work_evidence_sha256():
        raise ValueError("official work evidence SHA-256 mismatch")
    if ledger["live_diagnostic_receipt_sha256"] != LIVE_DIAGNOSTIC_RECEIPT_SHA256:
        raise ValueError("live diagnostic receipt SHA-256 mismatch")
    if ledger["approval_evidence_sha256"] != release_approval_evidence_sha256():
        raise ValueError("composite approval evidence SHA-256 mismatch")

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

    import_before = dict(import_row)
    import_after = dict(import_row)
    import_before["stem"] = before["stem"]
    import_after["stem"] = replacement["stem"]
    live_before = dict(import_before)
    live_after = dict(import_after)
    live_before.update(live_overrides)
    live_after.update(live_overrides)
    if canonical_cell(import_row.get("updatedAt", ""), "updatedAt") != "2026-04-10":
        raise ValueError("approved updatedAt source baseline changed")
    if row_sha256(live_before, import_headers) != ledger["expected_before_live_runtime_row_sha256"]:
        raise ValueError("approved live-before full-row hash mismatch")
    if row_sha256(live_after, import_headers) != ledger["expected_after_live_runtime_row_sha256"]:
        raise ValueError("approved live-after full-row hash mismatch")
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
        "live_before_hash": ledger["expected_before_live_runtime_row_sha256"],
        "live_after_hash": ledger["expected_after_live_runtime_row_sha256"],
        "live_overrides": live_overrides,
    }


def validate_official_approval_evidence() -> dict[str, object]:
    if not OFFICIAL_APPROVAL_EVIDENCE.is_file():
        raise ValueError("minimal official approval evidence is missing")
    try:
        evidence = json.loads(OFFICIAL_APPROVAL_EVIDENCE.read_text(encoding="utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("minimal official approval evidence is invalid") from exc
    fixed = {
        "evidenceStatus": "approved_official_source_review", "qId": QID,
        "officialSourceUrl": OFFICIAL_URL, "officialPdfSha256": OFFICIAL_PDF_SHA256,
        "questionPage1Based": int(OFFICIAL_PAGE), "sourceKind": OFFICIAL_SOURCE_KIND,
        "expectedLabelSequence": OFFICIAL_LABEL_SEQUENCE, "officialAnswerKey": "B",
        "officialAnswerNumber": 2, "fieldWhitelist": ["stem"], "protectedFieldCount": 29,
        "beforeStemSha256": OFFICIAL_BEFORE_STEM_SHA256,
        "replacementStemSha256": OFFICIAL_REPLACEMENT_STEM_SHA256,
        "sourceBeforeRowSha256": SOURCE_BEFORE_ROW_SHA256,
        "sourceAfterRowSha256": SOURCE_AFTER_ROW_SHA256,
        "importBeforeRowSha256": IMPORT_BEFORE_ROW_SHA256,
        "importAfterRowSha256": IMPORT_AFTER_ROW_SHA256,
        "priorWorkEvidenceSha256": PRIOR_WORK_EVIDENCE_SHA256,
        "reviewer": "independent_official_source_audit", "reviewedAt": "2026-08-22",
        "containsQuestionText": False, "containsPii": False,
    }
    if not isinstance(evidence, dict) or set(evidence) != set(fixed) or any(evidence.get(key) != value for key, value in fixed.items()):
        raise ValueError("minimal official approval evidence invariant mismatch")
    return evidence


def work_evidence_sha256() -> str:
    validate_official_approval_evidence()
    return evidence_sha256_for_paths([OFFICIAL_APPROVAL_EVIDENCE])


def validate_live_diagnostic_receipt() -> dict[str, object]:
    if not LIVE_DIAGNOSTIC_RECEIPT.is_file():
        raise ValueError("approved live diagnostic receipt is missing")
    raw = LIVE_DIAGNOSTIC_RECEIPT.read_bytes()
    actual_hash = hashlib.sha256(raw).hexdigest()
    if actual_hash != LIVE_DIAGNOSTIC_RECEIPT_SHA256:
        raise ValueError("approved live diagnostic receipt SHA-256 mismatch")
    try:
        receipt = json.loads(raw.decode("utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("approved live diagnostic receipt is invalid UTF-8 JSON") from exc
    if not isinstance(receipt, dict):
        raise ValueError("approved live diagnostic receipt must be an object")
    fixed = {
        "receiptStatus": "read_only_complete",
        "project": "takken-training",
        "target": QID,
        "sourceSha": "3429ceec1bd12bca5a6679286a28dd7ff64a6eb1",
        "productionVersion": 65,
        "readOnly": True,
        "maintenanceWindow": "ABSENT",
        "databaseChanged": False,
        "dbIdMatchesConfigured": True,
        "rowCount": ROW_COUNT,
        "uniqueQIds": ROW_COUNT,
        "targetMatches": 1,
        "nonTargetCount": ROW_COUNT - 1,
        "headerCount": 30,
        "liveRowSha256": LIVE_LEGACY_ROW_SHA256,
        "expectedRowSha256": "5531d591e1f07b2bc5b60c1e5f31b46e9723fd781ac2a31d11d12249d82f3919",
        "mismatchCount": 2,
        "mismatchFields": ["explainLong", "updatedAt"],
    }
    for key, expected in fixed.items():
        if receipt.get(key) != expected:
            raise ValueError(f"approved live diagnostic receipt invariant mismatch: {key}")
    checks = receipt.get("specialChecks") or {}
    if (checks.get("statusEqual") is not True or checks.get("sourceRefEqual") is not True or
            checks.get("explanationMismatchOnly") != "explainLong" or
            checks.get("dateSerializationMismatch") != "updatedAt" or
            checks.get("crlfMismatchFields") != []):
        raise ValueError("approved live diagnostic special checks mismatch")
    fields = receipt.get("fields")
    schema = receipt.get("fieldRecordSchema")
    if not isinstance(fields, list) or not isinstance(schema, list) or len(fields) != 30:
        raise ValueError("approved live diagnostic field evidence is incomplete")
    records = {record[0]: dict(zip(schema, record)) for record in fields if isinstance(record, list) and len(record) == len(schema)}
    if len(records) != 30 or set(receipt["mismatchFields"]) != {field for field, record in records.items() if record.get("equal") is not True}:
        raise ValueError("approved live diagnostic field mismatch inventory is inconsistent")
    if (records.get("stem", {}).get("liveNormalizedSha256") != OFFICIAL_BEFORE_STEM_SHA256 or
            records.get("explainLong", {}).get("liveNormalizedSha256") != sha256_text("") or
            records.get("updatedAt", {}).get("liveType") != "date" or
            receipt.get("updatedAtDisplaySha256") != sha256_text("2026-04-10")):
        raise ValueError("approved live diagnostic target/type evidence mismatch")
    return receipt


def release_approval_evidence_sha256() -> str:
    validate_live_diagnostic_receipt()
    return sha256_text(
        "r6-q28-release-approval-v2\n"
        f"official-work:{work_evidence_sha256()}\n"
        f"live-diagnostic-raw:{LIVE_DIAGNOSTIC_RECEIPT_SHA256}"
    )


def approved_ledger_from_work() -> dict[str, str]:
    """Revalidate the approved ledger against minimal tracked evidence.

    No text or answer is synthesized. The patch payload remains in the release
    ledger; the evidence bundle contains only source identity and hashes.
    """
    ledger = read_ledger(allow_missing_live_columns=True)
    validate_live_diagnostic_receipt()
    evidence = validate_official_approval_evidence()
    before_values = parse_payload(ledger.get("before_values_json", ""), "before_values_json")
    replacement_values = parse_payload(ledger.get("replacement_values_json", ""), "replacement_values_json")
    if set(before_values) != {"stem"} or set(replacement_values) != {"stem"}:
        raise ValueError("approved ledger payload must be stem-only")
    before_stem = canonical_text(before_values["stem"])
    replacement_stem = canonical_text(replacement_values["stem"])
    if sha256_text(before_stem) != evidence["beforeStemSha256"] or sha256_text(replacement_stem) != evidence["replacementStemSha256"]:
        raise ValueError("approved ledger stem hashes do not match minimal evidence")
    if re.findall(r"(?:^|\n)([アイウ])　", replacement_stem) != ["ア", "イ", "ウ"]:
        raise ValueError("approved replacement stem label sequence mismatch")

    source_headers, source_rows = read_dataset(SOURCE)
    import_headers, import_rows = read_dataset(IMPORT)
    source_current = find_target(source_rows, SOURCE.name)
    import_current = find_target(import_rows, IMPORT.name)
    for field in ("choiceA", "choiceB", "choiceC", "choiceD", "choiceE", "correct"):
        if source_current[field] != import_current[field]:
            raise ValueError(f"approved preserve field mismatch between planes: {field}")
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
    live_before = dict(import_before)
    live_after = dict(import_after)
    live_before.update(LIVE_BASELINE_OVERRIDES)
    live_after.update(LIVE_BASELINE_OVERRIDES)
    expected_before_live_runtime = row_sha256(live_before, import_headers)
    expected_after_live_runtime = row_sha256(live_after, import_headers)
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
        "expected_before_live_runtime_row_sha256": expected_before_live_runtime,
        "expected_after_live_runtime_row_sha256": expected_after_live_runtime,
        "live_baseline_overrides_json": json.dumps(LIVE_BASELINE_OVERRIDES, ensure_ascii=False, separators=(",", ":")),
        "live_date_only_fields": "updatedAt",
        "official_work_evidence_sha256": work_evidence_sha256(),
        "live_diagnostic_receipt_sha256": LIVE_DIAGNOSTIC_RECEIPT_SHA256,
        "reviewer": "independent_official_source_audit+independent_live_baseline_review",
        "reviewed_at": "2026-08-22",
        "approval_evidence_sha256": release_approval_evidence_sha256(),
        "notes": "Approved stem-only restoration with a separately evidenced live baseline. Live explainLong stays blank and updatedAt is date-only canonicalized; all 29 protected fields remain unchanged.",
    })
    return approved


def write_approved_ledger_from_work() -> None:
    approved = approved_ledger_from_work()
    with LEDGER.open("r", encoding="utf-8-sig", newline="") as handle:
        headers = list(csv.DictReader(handle).fieldnames or [])
    for column in LIVE_LEDGER_COLUMNS:
        if column not in headers:
            headers.append(column)
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
        "expectedBeforeRuntimeRowSha256": ledger["expected_before_live_runtime_row_sha256"],
        "expectedAfterRuntimeRowSha256": ledger["expected_after_live_runtime_row_sha256"],
        "sourceBeforeRuntimeRowSha256": ledger["expected_before_runtime_row_sha256"],
        "sourceAfterRuntimeRowSha256": ledger["expected_after_runtime_row_sha256"],
        "liveBaselineOverrides": validated.get("live_overrides", {}),
        "liveDateOnlyFields": [field for field in ledger.get("live_date_only_fields", "").split(",") if field],
        "liveDiagnosticReceiptSha256": ledger.get("live_diagnostic_receipt_sha256", ""),
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
