import argparse
import csv
import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data" / "takken_all_final.csv"
CURATED = ROOT / "data" / "takken_questionbank_import.csv"
ALLOWED_FIELDS = (
    "stem",
    "choiceA", "choiceB", "choiceC", "choiceD", "choiceE",
    "explainA", "explainB", "explainC", "explainD", "explainE",
    "explainShort", "explainLong",
)


def load_generator():
    path = ROOT / "tools" / "build_takken_import_csv.py"
    spec = importlib.util.spec_from_file_location("takken_builder", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read_rows(path):
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return reader.fieldnames, list(reader)


def main():
    parser = argparse.ArgumentParser(description="Merge reviewed import-only text edits into the tracked source CSV.")
    parser.add_argument("--apply", action="store_true", help="write the verified merge to takken_all_final.csv")
    parser.add_argument("--expected-changed-rows", type=int)
    parser.add_argument("--expected-changed-cells", type=int)
    parser.add_argument("--approve-qids", help="comma-separated exact qId allowlist for an applied merge")
    args = parser.parse_args()

    builder = load_generator()
    source_headers, source_rows = read_rows(SOURCE)
    curated_headers, curated_rows = read_rows(CURATED)
    builder.validate_headers(source_headers, "tracked source")
    builder.validate_headers(curated_headers, "reviewed import CSV")
    builder.validate_dataset(source_rows, "tracked source")
    builder.validate_dataset(curated_rows, "reviewed import CSV")
    builder.validate_structured_questions(curated_rows)
    curated_by_id = {row["qId"]: row for row in curated_rows}
    if len(curated_by_id) != 600 or set(curated_by_id) != {row["qId"] for row in source_rows}:
        raise ValueError("Source and curated qId sets differ")

    changed_rows = set()
    changed_cells = 0
    changed_fields = {}
    for row in source_rows:
        current_generated = builder.normalize_row(row)
        curated = curated_by_id[row["qId"]]
        for field in ALLOWED_FIELDS:
            if current_generated.get(field, "") == curated.get(field, ""):
                continue
            row[field] = curated.get(field, "")
            changed_rows.add(row["qId"])
            changed_cells += 1
            changed_fields.setdefault(row["qId"], []).append(field)

    regenerated = [builder.normalize_row(row) for row in source_rows]
    builder.validate_dataset(regenerated, "regenerated data")
    builder.validate_structured_questions(regenerated)
    differences = builder.compare_rows(regenerated, curated_rows)
    if differences:
        preview = "; ".join(f"{q_id}:{fields}" for q_id, fields in differences[:20])
        raise ValueError(f"Merge does not reproduce curated CSV ({len(differences)} rows): {preview}")

    for q_id in sorted(changed_fields):
        print(f"{q_id}: {','.join(changed_fields[q_id])}")
    print({"changedRows": len(changed_rows), "changedCells": changed_cells, "apply": args.apply})
    if not args.apply:
        return

    if args.expected_changed_rows is None or args.expected_changed_cells is None or args.approve_qids is None:
        raise ValueError(
            "--apply requires --expected-changed-rows, --expected-changed-cells, "
            "and --approve-qids"
        )
    approved_qids = {q_id.strip() for q_id in args.approve_qids.split(",") if q_id.strip()}
    if len(changed_rows) != args.expected_changed_rows:
        raise ValueError("Changed row count does not match explicit approval")
    if changed_cells != args.expected_changed_cells:
        raise ValueError("Changed cell count does not match explicit approval")
    if changed_rows != approved_qids:
        missing = sorted(changed_rows - approved_qids)
        extra = sorted(approved_qids - changed_rows)
        raise ValueError(f"Changed qIds do not match explicit approval; missing={missing}, extra={extra}")

    temp = SOURCE.with_suffix(SOURCE.suffix + ".tmp_sync")
    with temp.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=builder.HEADERS)
        writer.writeheader()
        writer.writerows(source_rows)
    temp.replace(SOURCE)


if __name__ == "__main__":
    main()
