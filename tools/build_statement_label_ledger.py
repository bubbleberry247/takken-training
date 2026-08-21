#!/usr/bin/env python3
"""Build the fixed, redacted ledger for the 51 approved label-only repairs.

The source-page cache is used only while creating the ledger, to prove the
statement boundaries.  The generated ledger contains hashes, offsets, source
metadata, and label order; it does not contain question text.  Runtime/source
patching uses the ledger and therefore does not depend on the external cache.
"""

from __future__ import annotations

import csv
import hashlib
import re
from pathlib import Path

from bs4 import BeautifulSoup


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
WORK = ROOT / "work" / "statement-label-audit-20260821"
SOURCE = DATA / "takken_all_final.csv"
OFFICIAL = WORK / "official_source_verification.csv"
CANDIDATES = WORK / "correction_candidates.csv"
DEST = DATA / "statement_label_corrections.csv"
CACHE = Path(r"C:\tmp\takken-statement-label-source-cache-20260821")

TARGET_COUNT = 51
EXCLUDED_QIDS = {"R6takken-028"}
FORBIDDEN_QIDS = {"R3atakken-038", "R3btakken-038"}
LABELS = tuple("アイウエ")
LEDGER_HEADERS = [
    "qId",
    "category",
    "official_source_url",
    "official_pdf_sha256",
    "pdf_page_1based",
    "source_kind",
    "source_ref",
    "source_hash",
    "expected_before_stem_sha256",
    "replacement_stem_sha256",
    "expected_label_sequence",
    "insertion_offsets",
    "source_statement_count",
    "protected_fields",
    "status",
]


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def canonical_text(value: str) -> str:
    return (value or "").replace("\r\n", "\n").replace("\r", "\n")


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def match_text(value: str) -> str:
    # Only transport whitespace and the known source/canonical percent-width
    # difference are ignored for boundary matching.  The actual canonical
    # text is never changed by this normalization.
    return re.sub(r"[\s\u3000]+", "", (value or "").replace("％", "%"))


def raw_index_map(raw: str) -> list[int]:
    return [index for index, char in enumerate(raw) if not re.match(r"[\s\u3000]", char)]


def source_items(source_ref: str) -> list[str]:
    cache_path = CACHE / f"{sha(source_ref)[:24]}.html"
    if not cache_path.exists():
        raise FileNotFoundError(f"source cache is missing: {cache_path}")
    soup = BeautifulSoup(cache_path.read_text(encoding="utf-8"), "html.parser")
    mondai = soup.select_one(".mondai")
    if mondai is None:
        raise ValueError(f"source has no .mondai container: {source_ref}")
    lists = mondai.select("ol.kanaList")
    if not lists:
        lists = [ol for ol in mondai.find_all("ol") if "selectList" not in (ol.get("class") or [])]
    if len(lists) != 1:
        raise ValueError(f"source statement list is ambiguous: {source_ref}")
    items = [" ".join(li.get_text(" ", strip=True).split()) for li in lists[0].find_all("li", recursive=False)]
    if not items:
        raise ValueError(f"source statement list is empty: {source_ref}")
    return items


def locate_insertions(raw: str, items: list[str], labels: list[str]) -> tuple[list[int], str]:
    normalized = match_text(raw)
    mapping = raw_index_map(raw)
    cursor = 0
    starts: list[int] = []
    for item in items:
        needle = match_text(item)
        position = normalized.find(needle, cursor)
        if position < 0:
            raise ValueError("source statement does not occur sequentially in canonical stem")
        starts.append(mapping[position])
        cursor = position + len(needle)
    if len(starts) != len(labels):
        raise ValueError(f"source statement count/label count mismatch: {len(starts)} != {len(labels)}")

    corrected = raw
    for start, label in sorted(zip(starts, labels), reverse=True):
        corrected = corrected[:start] + "\n\n" + label + "\u3000" + corrected[start:]
    return starts, corrected


def main() -> None:
    official_rows = read_rows(OFFICIAL)
    candidate_rows = read_rows(CANDIDATES)
    source_rows = read_rows(SOURCE)
    official = {row["qId"]: row for row in official_rows}
    candidates = {row["qId"]: row for row in candidate_rows}
    source = {row["qId"]: row for row in source_rows}

    target_ids = {
        row["qId"] for row in official_rows if row.get("status") == "confirmed_missing"
    }
    if len(target_ids) != TARGET_COUNT:
        raise ValueError(f"expected {TARGET_COUNT} confirmed_missing qIds, got {len(target_ids)}")
    if target_ids & EXCLUDED_QIDS:
        raise ValueError("blocked qId is present in the correction target set")
    if target_ids & FORBIDDEN_QIDS:
        raise ValueError("R3 Q38 qId must not be re-updated by this ledger")
    if target_ids != set(candidates):
        raise ValueError("official and correction-candidate qId sets differ")

    ledger: list[dict[str, str]] = []
    for q_id in sorted(target_ids):
        official_row = official[q_id]
        candidate = candidates[q_id]
        canonical = canonical_text(source[q_id]["stem"])
        expected_before = sha(canonical)
        if expected_before != candidate["canonical_stem_hash"]:
            raise ValueError(f"canonical before hash mismatch: {q_id}")
        if candidate.get("status") != "manual_review":
            raise ValueError(f"candidate status is not manual_review: {q_id}")
        sequence = official_row["label_sequence"]
        labels = sequence.split("・")
        if labels not in [list(LABELS[:3]), list(LABELS[:4])]:
            raise ValueError(f"unexpected label sequence: {q_id}: {sequence}")
        if official_row.get("correction_approval") != "label_only_candidate":
            raise ValueError(f"official approval mismatch: {q_id}")
        items = source_items(candidate["source_ref"])
        starts, corrected = locate_insertions(canonical, items, labels)
        ledger.append({
            "qId": q_id,
            "category": official_row["category"],
            "official_source_url": official_row["official_source_url"],
            "official_pdf_sha256": official_row["official_pdf_sha256"],
            "pdf_page_1based": official_row["pdf_page_1based"],
            "source_kind": official_row["source_kind"],
            "source_ref": candidate["source_ref"],
            "source_hash": candidate["source_hash"],
            "expected_before_stem_sha256": expected_before,
            "replacement_stem_sha256": sha(corrected),
            "expected_label_sequence": sequence,
            "insertion_offsets": ";".join(str(start) for start in starts),
            "source_statement_count": str(len(items)),
            "protected_fields": "choiceA-D,choiceE,correct,explain*,imageUrl,choiceImageUrl,source_ref",
            "status": "approved_label_only_patch",
        })

    with DEST.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=LEDGER_HEADERS, lineterminator="\r\n")
        writer.writeheader()
        writer.writerows(ledger)
    print({"rows": len(ledger), "dest": str(DEST), "excluded": sorted(EXCLUDED_QIDS)})


if __name__ == "__main__":
    main()
