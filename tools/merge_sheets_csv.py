"""
Merge script: combine best data from production Sheets and working CSV.

Base = Sheets (30 columns including choiceImageUrl)
Patches = CSV (29 columns, no choiceImageUrl)
Cross-reference = sheets_csv_ng_crossref.csv (category per qId)

Merge rules: see user specification.
"""

import csv
import sys
from pathlib import Path
from collections import defaultdict

# ── File paths ──
SHEETS_PATH = Path(r"C:\Users\owner\Downloads\Doboku14W_DB_20260215 - QuestionBank.csv")
CSV_PATH = Path(r"c:\ProgramData\Generative AI\Github\doboku-14w-training\tools\questionbank_drive_import.csv")
CROSSREF_PATH = Path(r"C:\tmp\sheets_csv_ng_crossref.csv")
OUTPUT_PATH = Path(r"c:\ProgramData\Generative AI\Github\doboku-14w-training\tools\questionbank_merged.csv")

# ── Sheets column order (30 columns) ──
SHEETS_COLUMNS = [
    "qId", "segmentId", "type", "difficulty", "tag1", "tag2", "tag3",
    "lawTag", "revisionFlag", "conceptId", "variantGroupId", "source_ref",
    "imageUrl", "choiceImageUrl", "stem", "choiceA", "choiceB", "choiceC",
    "choiceD", "choiceE", "explainA", "explainB", "explainC", "explainD",
    "explainE", "correct", "explainShort", "explainLong", "status", "updatedAt"
]

EXPLAIN_FIELDS = ["explainA", "explainB", "explainC", "explainD", "explainE", "explainShort"]

# 21 qIds where Sheets explains are better (CSV is regression)
SHEETS_OK_CSV_NG_IDS = set()

# Stats
stats = defaultdict(int)


def load_csv_as_dict(path, encoding="utf-8"):
    """Load CSV into dict keyed by qId."""
    data = {}
    with open(path, "r", encoding=encoding, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Strip BOM from qId key if present
            qid = None
            for key in row:
                clean_key = key.lstrip("\ufeff").strip()
                if clean_key == "qId":
                    qid = row[key].strip()
                    break
            if qid:
                # Normalize all keys
                clean_row = {}
                for key, val in row.items():
                    clean_key = key.lstrip("\ufeff").strip()
                    clean_row[clean_key] = val
                data[qid] = clean_row
    return data


def load_crossref(path):
    """Load cross-reference into dict: qId -> category."""
    cats = {}
    with open(path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            qid = row["qId"].strip()
            cat = row["category"].strip()
            cats[qid] = cat
    return cats


def pick_longer(sheets_val, csv_val):
    """Return the longer non-empty string, preferring Sheets on tie."""
    s = (sheets_val or "").strip()
    c = (csv_val or "").strip()
    if not s and not c:
        return sheets_val  # both empty
    if not s:
        return csv_val
    if not c:
        return sheets_val
    if len(c) > len(s):
        return csv_val
    return sheets_val  # Sheets wins on tie or when longer


def merge():
    print("Loading files...")
    sheets_data = load_csv_as_dict(SHEETS_PATH, encoding="utf-8")
    csv_data = load_csv_as_dict(CSV_PATH, encoding="utf-8-sig")
    crossref = load_crossref(CROSSREF_PATH)

    # Build SHEETS_OK_CSV_NG set from crossref
    for qid, cat in crossref.items():
        if cat == "SHEETS_OK_CSV_NG":
            SHEETS_OK_CSV_NG_IDS.add(qid)

    print(f"Sheets: {len(sheets_data)} questions")
    print(f"CSV: {len(csv_data)} questions")
    print(f"Cross-ref: {len(crossref)} entries")
    print(f"SHEETS_OK_CSV_NG: {len(SHEETS_OK_CSV_NG_IDS)} qIds")

    # Verify all Sheets qIds are present
    missing_in_csv = set(sheets_data.keys()) - set(csv_data.keys())
    if missing_in_csv:
        print(f"WARNING: {len(missing_in_csv)} qIds in Sheets but not in CSV: {sorted(missing_in_csv)[:5]}...")

    merged_rows = []

    for qid in sorted(sheets_data.keys()):
        sh = sheets_data[qid]
        cv = csv_data.get(qid, {})
        cat = crossref.get(qid, "BOTH_OK")  # Default to BOTH_OK if not in crossref

        # Start with Sheets as base
        merged = {}
        for col in SHEETS_COLUMNS:
            merged[col] = sh.get(col, "")

        # ── Rule 1: Base fields from Sheets (already done above) ──
        # segmentId, type, difficulty, choiceA-E, choiceImageUrl, lawTag,
        # revisionFlag, conceptId, variantGroupId, source_ref, status, updatedAt
        # These stay as Sheets values.

        # ── Rule 2: correct ──
        if qid == "R1gakkaA-004" and cv:
            stats["correct_from_csv"] += 1
            merged["correct"] = cv.get("correct", merged["correct"])
        else:
            stats["correct_from_sheets"] += 1
            # Keep Sheets

        # ── Rule 3: imageUrl from CSV ──
        if cv:
            csv_img = (cv.get("imageUrl") or "").strip()
            sheets_img = (sh.get("imageUrl") or "").strip()
            if csv_img:
                if csv_img != sheets_img:
                    stats["imageUrl_from_csv"] += 1
                else:
                    stats["imageUrl_same"] += 1
                merged["imageUrl"] = csv_img
            else:
                stats["imageUrl_from_sheets"] += 1
        else:
            stats["imageUrl_from_sheets"] += 1

        # ── Rule 4: tag1 from Sheets ──
        stats["tag1_from_sheets"] += 1

        # ── Rule 5: tag2, tag3 ──
        for tag_field in ["tag2", "tag3"]:
            sheets_val = (sh.get(tag_field) or "").strip()
            csv_val = (cv.get(tag_field) or "").strip() if cv else ""
            if not sheets_val and csv_val:
                merged[tag_field] = csv_val
                stats[f"{tag_field}_from_csv"] += 1
            else:
                stats[f"{tag_field}_from_sheets"] += 1

        # ── Stem field: special logic ──
        if cv:
            sheets_stem = (sh.get("stem") or "").strip()
            csv_stem = (cv.get("stem") or "").strip()
            use_csv_stem = False

            # If CSV stem is longer by 30+ chars (truncation fix)
            if len(csv_stem) > len(sheets_stem) + 30:
                use_csv_stem = True
                stats["stem_csv_longer"] += 1

            if use_csv_stem:
                merged["stem"] = csv_stem
                stats["stem_from_csv"] += 1
            else:
                stats["stem_from_sheets"] += 1
        else:
            stats["stem_from_sheets"] += 1

        # ── Explain fields: depends on category ──
        if cat == "SHEETS_OK_CSV_NG":
            # Keep Sheets explains (CSV is regression)
            for ef in EXPLAIN_FIELDS:
                stats[f"{ef}_from_sheets"] += 1
            stats["explain_category_sheets_ok_csv_ng"] += 1

        elif cat == "SHEETS_NG_CSV_OK":
            # Use CSV explains
            for ef in EXPLAIN_FIELDS:
                if cv:
                    merged[ef] = cv.get(ef, merged[ef])
                    stats[f"{ef}_from_csv"] += 1
                else:
                    stats[f"{ef}_from_sheets"] += 1
            stats["explain_category_sheets_ng_csv_ok"] += 1

        elif cat == "BOTH_NG":
            # Use CSV explains (better than Sheets)
            for ef in EXPLAIN_FIELDS:
                if cv:
                    merged[ef] = cv.get(ef, merged[ef])
                    stats[f"{ef}_from_csv"] += 1
                else:
                    stats[f"{ef}_from_sheets"] += 1
            stats["explain_category_both_ng"] += 1

        elif cat == "BOTH_OK":
            # Use longer of Sheets vs CSV for each explain field
            for ef in EXPLAIN_FIELDS:
                if cv:
                    sheets_val = sh.get(ef, "")
                    csv_val = cv.get(ef, "")
                    result = pick_longer(sheets_val, csv_val)
                    if result == csv_val and csv_val != sheets_val:
                        stats[f"{ef}_from_csv"] += 1
                    else:
                        stats[f"{ef}_from_sheets"] += 1
                    merged[ef] = result
                else:
                    stats[f"{ef}_from_sheets"] += 1
            stats["explain_category_both_ok"] += 1

        else:
            # Unknown category - keep Sheets
            for ef in EXPLAIN_FIELDS:
                stats[f"{ef}_from_sheets"] += 1
            stats["explain_category_unknown"] += 1

        merged_rows.append(merged)

    # ── Write output ──
    print(f"\nWriting {len(merged_rows)} rows to {OUTPUT_PATH}")
    with open(OUTPUT_PATH, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=SHEETS_COLUMNS, quoting=csv.QUOTE_ALL)
        writer.writeheader()
        writer.writerows(merged_rows)

    # ── Print statistics ──
    print("\n" + "=" * 60)
    print("MERGE STATISTICS")
    print("=" * 60)

    print(f"\nTotal questions merged: {len(merged_rows)}")

    print("\n--- correct field ---")
    print(f"  From Sheets: {stats['correct_from_sheets']}")
    print(f"  From CSV (R1gakkaA-004 only): {stats['correct_from_csv']}")

    print("\n--- imageUrl field ---")
    print(f"  From CSV (different): {stats['imageUrl_from_csv']}")
    print(f"  Same in both: {stats['imageUrl_same']}")
    print(f"  From Sheets (CSV empty): {stats['imageUrl_from_sheets']}")

    print("\n--- tag fields ---")
    print(f"  tag1: always Sheets ({stats['tag1_from_sheets']})")
    print(f"  tag2 from Sheets: {stats['tag2_from_sheets']}, from CSV: {stats['tag2_from_csv']}")
    print(f"  tag3 from Sheets: {stats['tag3_from_sheets']}, from CSV: {stats['tag3_from_csv']}")

    print("\n--- stem field ---")
    print(f"  From Sheets: {stats['stem_from_sheets']}")
    print(f"  From CSV (longer by 30+): {stats['stem_from_csv']}")
    if stats.get('stem_csv_longer'):
        print(f"    (truncation fixes: {stats['stem_csv_longer']})")

    print("\n--- explain fields (by category) ---")
    print(f"  BOTH_OK (longer wins): {stats['explain_category_both_ok']}")
    print(f"  SHEETS_NG_CSV_OK (CSV): {stats['explain_category_sheets_ng_csv_ok']}")
    print(f"  BOTH_NG (CSV): {stats['explain_category_both_ng']}")
    print(f"  SHEETS_OK_CSV_NG (Sheets): {stats['explain_category_sheets_ok_csv_ng']}")
    if stats.get('explain_category_unknown'):
        print(f"  Unknown (Sheets): {stats['explain_category_unknown']}")

    print("\n--- explain field sources (per field) ---")
    for ef in EXPLAIN_FIELDS:
        s_count = stats.get(f"{ef}_from_sheets", 0)
        c_count = stats.get(f"{ef}_from_csv", 0)
        print(f"  {ef}: Sheets={s_count}, CSV={c_count}")

    # Overall summary
    total_sheets = 0
    total_csv = 0
    for key, val in stats.items():
        if key.endswith("_from_sheets"):
            total_sheets += val
        elif key.endswith("_from_csv"):
            total_csv += val
    print(f"\n--- Overall field picks ---")
    print(f"  Total fields from Sheets: {total_sheets}")
    print(f"  Total fields from CSV: {total_csv}")
    print(f"  (Excludes base fields always from Sheets: segmentId, type, difficulty, choices, etc.)")

    # Verify R1gakkaA-004 correct value
    for row in merged_rows:
        if row["qId"] == "R1gakkaA-004":
            print(f"\n--- Verification: R1gakkaA-004 ---")
            print(f"  correct = {row['correct']}")
            break

    print(f"\nOutput saved to: {OUTPUT_PATH}")
    print("Done!")


if __name__ == "__main__":
    merge()
