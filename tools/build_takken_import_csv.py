import csv
import hashlib
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data" / "takken_all_final.csv"
DEST = ROOT / "data" / "takken_questionbank_import.csv"

HEADERS = [
    "qId", "segmentId", "type", "difficulty",
    "tag1", "tag2", "tag3", "lawTag",
    "revisionFlag", "conceptId", "variantGroupId", "source_ref",
    "imageUrl", "choiceImageUrl",
    "stem", "choiceA", "choiceB", "choiceC", "choiceD", "choiceE",
    "explainA", "explainB", "explainC", "explainD", "explainE",
    "correct", "explainShort", "explainLong", "status", "updatedAt",
]

SEGMENT_BY_MAJOR = {
    "権利関係": "takken_rights",
    "法令上の制限": "takken_law",
    "宅地建物取引業法等": "takken_business",
    "税・その他": "takken_other",
}

TAG_TO_MAJOR = {
    "権利関係": "権利関係",
    "借地借家法": "権利関係",
    "借地借家法（建物）": "権利関係",
    "権利関係（意思表示）": "権利関係",
    "不動産登記法": "権利関係",
    "区分所有法": "権利関係",
    "法令上の制限": "法令上の制限",
    "建築基準法": "法令上の制限",
    "都市計画法": "法令上の制限",
    "国土利用計画法": "法令上の制限",
    "宅地建物取引業法等": "宅地建物取引業法等",
    "不当景品類及び不当表示防止法": "税・その他",
    "土地と建物及びその需給": "税・その他",
    "税に関する法令": "税・その他",
    "不動産価格の評定": "税・その他",
    "不動産取得税": "税・その他",
    "税・その他": "税・その他",
}

COUNT_QUESTION_IDS = {
    "R5takken-006", "R5takken-026", "R5takken-030", "R5takken-034",
    "R5takken-036", "R5takken-038", "R5takken-042", "R6takken-006",
    "R6takken-026", "R6takken-037", "R6takken-041", "R3atakken-038",
    "R7takken-003",
    "R7takken-028", "R7takken-030", "R7takken-031", "R7takken-033",
    "R7takken-036", "R7takken-038", "R7takken-040", "R7takken-042",
    "R7takken-043",
}

COMBINATION_QUESTION_IDS = {
    "R3btakken-038", "R5takken-004", "R7takken-005", "R7takken-026",
}

COUNT_CHOICES_FOUR = ("一つ", "二つ", "三つ", "四つ")
COUNT_CHOICES_NONE = ("一つ", "二つ", "三つ", "なし")
STRUCTURED_QUESTION_FIXTURES = {
    "R3atakken-038": (COUNT_CHOICES_FOUR, "D"),
    "R3btakken-038": (("ア、イ", "ア、エ", "イ、ウ", "ウ、エ"), "C"),
    "R5takken-004": (("ア、イ、ウ", "イ、ウ", "ウ、エ", "エ"), "D"),
    "R5takken-006": (COUNT_CHOICES_NONE, "C"),
    "R5takken-026": (COUNT_CHOICES_FOUR, "C"),
    "R5takken-030": (COUNT_CHOICES_FOUR, "A"),
    "R5takken-034": (COUNT_CHOICES_FOUR, "C"),
    "R5takken-036": (COUNT_CHOICES_FOUR, "C"),
    "R5takken-038": (COUNT_CHOICES_FOUR, "B"),
    "R5takken-042": (COUNT_CHOICES_FOUR, "C"),
    "R6takken-006": (COUNT_CHOICES_NONE, "D"),
    "R6takken-026": (COUNT_CHOICES_FOUR, "C"),
    "R6takken-037": (COUNT_CHOICES_FOUR, "C"),
    "R6takken-041": (COUNT_CHOICES_NONE, "A"),
    "R7takken-003": (COUNT_CHOICES_FOUR, "C"),
    "R7takken-005": (("ア、エ", "イ、ウ", "ア、ウ、エ", "ア、イ、ウ"), "D"),
    "R7takken-026": (("ア、イ", "イ、ウ", "ア、ウ", "ア、イ、ウ"), "D"),
    "R7takken-028": (COUNT_CHOICES_NONE, "B"),
    "R7takken-030": (COUNT_CHOICES_FOUR, "C"),
    "R7takken-031": (COUNT_CHOICES_FOUR, "D"),
    "R7takken-033": (COUNT_CHOICES_FOUR, "C"),
    "R7takken-036": (COUNT_CHOICES_FOUR, "D"),
    "R7takken-038": (COUNT_CHOICES_FOUR, "C"),
    "R7takken-040": (COUNT_CHOICES_NONE, "C"),
    "R7takken-042": (COUNT_CHOICES_FOUR, "B"),
    "R7takken-043": (COUNT_CHOICES_FOUR, "D"),
}
STRUCTURED_STEM_SHA256 = {
    "R3atakken-038": "09e45de1f487dc734b364c9f2b81bac3288781df1455c1ef0d0d4e9f25413399",
    "R3btakken-038": "c208d30ca29b7fb1ab2305b7f17f9f1eae379e0b920b320c77ec79c36692a2fa",
    "R5takken-004": "6b0de46e6e8157bb5234f3c980667b131fd3e4d227a45a43b5e2c550e41b3122",
    "R5takken-006": "b04e2d9c4fe8b69074561b6996d53623b0d98caefb225f71dc595f13c79e4251",
    "R5takken-026": "694438209d9ce00c8e2c5637207005d6208c5b3ba3cabdfc65d82b9785cb594d",
    "R5takken-030": "e48c9f1e11cea5c6a8e82fd841e79bbbf2e765db30865a912fa786dbf88240fe",
    "R5takken-034": "9a8f030c960ce5e1debddeec56b07b2b2178a6ecec8aa854d112fae655834da6",
    "R5takken-036": "143113aac1ad7aefd0dedfef40e4cc10a3f5c39ff701c0af3001b7d8d86c8510",
    "R5takken-038": "ccf42bd454dbb76a2672b5863597ced60f01cf48e2f9afc104c458e8c37a89ed",
    "R5takken-042": "183a46625a39b08aa2aa69f34f58e4b9bc5f6a5c96c0f29211fac56c7722cdd1",
    "R6takken-006": "0c93815c84fc4fe664559725c55e90833f5066016996ddb50448eede9279b835",
    "R6takken-026": "773a0eb9968cf4d5dee0131682e81f7a9554a6fe37d93e09970c62ab5194999f",
    "R6takken-037": "9fea938e05966a1db7addbde86a16f9bc8611d213f06cb54402f379972440172",
    "R6takken-041": "7d1f6ee8f2697ee40e9b8e26d1e22ae612b9b16b07098e01936b3efef0387ed4",
    "R7takken-003": "b0cf325e182330f2b1b75e00cf6cfd4fe2977daa4cdbc3ad2996f2b3ad5083bf",
    "R7takken-005": "2415be6dae90e4785bfad369c1db22c84b43b4b353f46b33818be7b3366bb36e",
    "R7takken-026": "79d51fcd2e61d282055b83ada948488632f31d3f85aa96d99a893c1aa293dcad",
    "R7takken-028": "64d40d924b80ed736f311f3bd8deeded98e57de9d1e5148f8a7d01379bb3bfb0",
    "R7takken-030": "b3c395d12054e6f30ebdc122539fffd713ee369c1875832668d8ad21eedd79bb",
    "R7takken-031": "7f48ccef7f72bee0e874e6b2d2c782feac97e502538591b38aca68e5e5a5ca1a",
    "R7takken-033": "2e4b7e4f2fbf1d721b9f3126ad99d49940156aef1b66b9820cf83b6eb9ea82e7",
    "R7takken-036": "9428898c0e85dc32d6086bfde8afb20ef464a7f23a68f835b961debb1b89f851",
    "R7takken-038": "8b9377cff3a100992aeb55b167a840ea3f0ef16c4414794d01fcc6d7b0fae7d3",
    "R7takken-040": "5571669762758d4c57043cdfa14aaa687b5e0f1cd6d6a9881a9c2e7ee433a9cd",
    "R7takken-042": "14771d0da6ce92891c0b700ee29ca5e9daa6c1e3f6b30236e6e7bb9f7edc4a11",
    "R7takken-043": "70ab46077c8a174bc069f50cc2faebe016286b37136104c2f8f174999cfee17a",
}


def normalize_row(row):
    original_tag = (row.get("tag1") or "").strip()
    major = TAG_TO_MAJOR.get(original_tag, "税・その他")
    year = (row.get("qId") or "").split("takken-", 1)[0]

    out = {key: (row.get(key) or "").strip() for key in HEADERS}
    out["segmentId"] = SEGMENT_BY_MAJOR[major]
    out["type"] = "knowledge"
    out["difficulty"] = out["difficulty"] or "3"
    out["tag1"] = major
    out["tag2"] = original_tag if original_tag and original_tag != major else year
    out["tag3"] = year if out["tag2"] != year else ""
    out["revisionFlag"] = out["revisionFlag"] if out["revisionFlag"] in {"0", "1"} else "0"
    out["variantGroupId"] = out["variantGroupId"] or out["qId"]
    out["correct"] = out["correct"].upper()
    if not out["explainShort"]:
        first_correct = out["correct"].split(",", 1)[0].strip().upper()
        correct_explain = out.get("explain" + first_correct, "")
        out["explainShort"] = out["explainLong"] or correct_explain
    if not out["explainShort"]:
        out["explainShort"] = "解説は今後補足予定です。"
    out["status"] = "published"
    out["updatedAt"] = out["updatedAt"] or "2026-04-10"
    return out


def validate_structured_questions(rows):
    by_id = {row["qId"]: row for row in rows}
    expected = COUNT_QUESTION_IDS | COMBINATION_QUESTION_IDS
    missing = sorted(expected - set(by_id))
    if missing:
        raise ValueError("Missing structured qIds: " + ", ".join(missing))

    marker_labels = ("ア", "イ", "ウ")
    for q_id in sorted(expected):
        row = by_id[q_id]
        choices = tuple(row.get("choice" + key, "") for key in "ABCD")
        expected_choices, expected_correct = STRUCTURED_QUESTION_FIXTURES[q_id]
        if (
            choices != expected_choices
            or row.get("choiceE", "") != ""
            or row.get("correct", "") != expected_correct
        ):
            raise ValueError(f"Structured answer fixture mismatch: {q_id}")
        stem = row.get("stem", "")
        if not all(marker in stem for marker in marker_labels):
            raise ValueError(f"Structured statements are missing from stem: {q_id}")
        canonical_stem = stem.replace("\r\n", "\n").replace("\r", "\n")
        stem_hash = hashlib.sha256(canonical_stem.encode("utf-8")).hexdigest()
        if stem_hash != STRUCTURED_STEM_SHA256[q_id]:
            raise ValueError(f"Structured stem fixture mismatch: {q_id}")


def validate_dataset(rows, label):
    q_ids = [row.get("qId", "") for row in rows]
    if len(rows) != 600 or len(set(q_ids)) != 600 or any(not q_id for q_id in q_ids):
        raise ValueError(f"Expected 600 unique nonblank questions in {label}")


def validate_headers(fieldnames, label):
    actual = list(fieldnames or [])
    if actual != HEADERS:
        raise ValueError(f"Unexpected CSV schema in {label}: {actual}")


def compare_rows(expected, actual):
    actual_by_id = {row.get("qId", ""): row for row in actual}
    differences = []
    for row in expected:
        other = actual_by_id.get(row["qId"])
        if other is None:
            differences.append((row["qId"], "missing"))
            continue
        changed = [key for key in HEADERS if row.get(key, "") != other.get(key, "")]
        if changed:
            differences.append((row["qId"], ",".join(changed)))
    extra = sorted(set(actual_by_id) - {row["qId"] for row in expected})
    differences.extend((q_id, "extra") for q_id in extra)
    return differences


def main():
    with SRC.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        validate_headers(reader.fieldnames, "tracked source")
        rows = list(reader)

    normalized = [normalize_row(row) for row in rows]
    validate_dataset(normalized, "generated data")
    validate_structured_questions(normalized)

    if "--check" in sys.argv:
        if not DEST.exists():
            raise FileNotFoundError(f"Missing generated CSV: {DEST}")
        with DEST.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            validate_headers(reader.fieldnames, "generated CSV")
            current = list(reader)
        validate_dataset(current, "generated CSV")
        differences = compare_rows(normalized, current)
        if differences:
            preview = "; ".join(f"{q_id}:{fields}" for q_id, fields in differences[:20])
            raise SystemExit(f"Generated CSV is stale ({len(differences)} rows): {preview}")
        print({"rows": len(normalized), "check": "ok", "dest": str(DEST)})
        return

    with DEST.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=HEADERS)
        writer.writeheader()
        writer.writerows(normalized)

    counts = {}
    for row in normalized:
        counts[row["segmentId"]] = counts.get(row["segmentId"], 0) + 1
    print({"rows": len(normalized), "dest": str(DEST), "segments": counts})


if __name__ == "__main__":
    main()
