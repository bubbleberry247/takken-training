from __future__ import annotations

import csv
import hashlib
import json
import re
from pathlib import Path

from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[2]
WORK = Path(__file__).resolve().parent
QID = "R6takken-028"

OFFICIAL_ARCHIVE_URL = "https://www.retio.or.jp/exam/past_ques_ans/other/"
OFFICIAL_PDF_URL = "https://www.retio.or.jp/wp-content/uploads/2025/03/R6_question_answer.pdf"
OFFICIAL_PDF_SHA256 = "82a95815f991567ebc4982b05a15a71f6ec942bd6794c3bafe3bcf9c2e985bae"
OFFICIAL_PDF = Path(r"C:\tmp\takken-official-audit-20260807\R6_question_answer.pdf")
OFFICIAL_PAGE_IMAGE = Path(
    r"C:\Users\owner\AppData\Local\Temp\takken-official-pdfs-20260821\rendered\R6-page16.png"
)
OFFICIAL_PAGE_IMAGE_SHA256 = "46143e24f98c8f81e8d93613352dde7fd1516abe0f2b5b7b5c461f6c5e1c8f68"

# Work-only transcription from the hash-verified official page image. The PDF's
# Japanese text layer is not usable as an independent character-level oracle;
# do not claim an automated text-layer comparison that this script cannot prove.
OFFICIAL_STEM = (
    "宅地建物取引業者Ａ（消費税課税事業者）及び宅地建物取引業者Ｂ（消費税免税事業者）"
    "が受領した報酬に関するアからウの記述のうち、宅地建物取引業法の規定に違反しないものの"
    "組合せは1から4のうちどれか。なお、代理、媒介に当たり、広告の依頼は行われていないものとする。\n"
    "ア　居住用建物（1か月の借賃12万円。消費税等相当額を含まない。）について、Ａは貸主から代理を依頼され、"
    "Ｂは借主から媒介を依頼され、Ａは貸主から6.7万円、Ｂは借主から6.5万円を報酬として受領した。"
    "なお、Ｂは、媒介の依頼を受けるに当たって、報酬について借主から特段の承諾を得ていない。\n"
    "イ　Ｂは、事業用建物について、貸主と借主双方から媒介を依頼され、借賃1か月分10万円"
    "（消費税等相当額を含まない。）、権利金90万円（権利設定の対価として支払われる金銭であって"
    "返還されないもので、消費税等相当額を含まない。）の賃貸借契約を成立させ、貸主と借主から"
    "それぞれ5万円を報酬として受領した。\n"
    "ウ　Ａは、土地付建物について、売主と買主双方から媒介を依頼され、代金3,500万円"
    "（消費税等相当額を含み、土地代金は2,400万円である。）の売買契約を成立させ、売主と買主から"
    "それぞれ110万円を報酬として受領したほか、売主の特別の依頼に基づき行った遠隔地への現地調査に"
    "要した実費の費用について、売主が事前に負担を承諾していたので、売主から9万円を受領した。"
)

OFFICIAL_CHOICES = {
    "choiceA": "ア、イ",
    "choiceB": "イ、ウ",
    "choiceC": "ア、ウ",
    "choiceD": "ア、イ、ウ",
    "choiceE": "",
}
OFFICIAL_CORRECT_NUMBER = "2"
OFFICIAL_CORRECT_KEY = "B"

INPUTS = {
    "canonical": ROOT / "data" / "takken_all_final.csv",
    "import": ROOT / "data" / "takken_questionbank_import.csv",
    "last_deploy_bundle": Path(r"C:\tmp\gas-deploy-20260807-1\takken\data\takken_questionbank_import.csv"),
}
PRODUCTION_RECEIPT = ROOT / "work" / "deploy-receipts" / "20260822-014347-takken-production.json"

FIELDS = [
    "stem",
    "choiceA",
    "choiceB",
    "choiceC",
    "choiceD",
    "choiceE",
    "correct",
    "explainA",
    "explainB",
    "explainC",
    "explainD",
    "explainE",
    "explainShort",
    "explainLong",
    "imageUrl",
    "choiceImageUrl",
    "source_ref",
    "status",
]


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def text_hash(value: str) -> str:
    return sha256_bytes(value.replace("\r\n", "\n").encode("utf-8"))


def read_row(path: Path) -> dict[str, str]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = [row for row in csv.DictReader(handle) if row.get("qId") == QID]
    if len(rows) != 1:
        raise AssertionError(f"{path}: expected exactly one {QID}, got {len(rows)}")
    return {key: (value or "") for key, value in rows[0].items()}


def redact_value(value: str) -> str:
    return "" if not value else f"sha256:{text_hash(value)};chars:{len(value)}"


def main() -> None:
    if sha256_bytes(OFFICIAL_PDF.read_bytes()) != OFFICIAL_PDF_SHA256:
        raise AssertionError("official PDF hash mismatch")
    if sha256_bytes(OFFICIAL_PAGE_IMAGE.read_bytes()) != OFFICIAL_PAGE_IMAGE_SHA256:
        raise AssertionError("official page image hash mismatch")

    answer_text = PdfReader(str(OFFICIAL_PDF)).pages[28].extract_text()
    answer_numbers = re.findall(r"[1-4]", answer_text)
    if len(answer_numbers) != 50:
        raise AssertionError(f"expected 50 official answers, got {len(answer_numbers)}")
    if answer_numbers[27] != OFFICIAL_CORRECT_NUMBER:
        raise AssertionError("official Q28 answer mismatch")

    rows = {name: read_row(path) for name, path in INPUTS.items()}
    baseline = rows["last_deploy_bundle"]
    for name in ("canonical", "import"):
        row = rows[name]
        for field in FIELDS:
            if field != "stem" and row.get(field, "") != baseline.get(field, ""):
                raise AssertionError(f"{name}.{field} differs from protected deploy baseline")
        if row.get("stem", "") not in {baseline["stem"], OFFICIAL_STEM}:
            raise AssertionError(f"{name}.stem is neither approved before nor approved after")
    if rows["canonical"]["stem"] != rows["import"]["stem"]:
        raise AssertionError("canonical/import are on different restoration states")
    local_state = "after" if rows["canonical"]["stem"] == OFFICIAL_STEM else "before"

    for field, expected in OFFICIAL_CHOICES.items():
        if baseline.get(field, "") != expected:
            raise AssertionError(f"{field} differs from official option")
    if baseline["correct"] != OFFICIAL_CORRECT_KEY:
        raise AssertionError("current correct key differs from official answer")
    if baseline.get("imageUrl", "") or baseline.get("choiceImageUrl", ""):
        raise AssertionError("current record unexpectedly references an image")
    if re.findall(r"(?:^|\n)([アイウ])　", OFFICIAL_STEM) != ["ア", "イ", "ウ"]:
        raise AssertionError("official transcription label sequence mismatch")
    if "長期の空家等" not in baseline["stem"]:
        raise AssertionError("expected post-exam qualification missing from old stem")
    if "長期の空家等" in OFFICIAL_STEM:
        raise AssertionError("official exam stem must not contain post-exam qualification")

    # Existing explanations are not official commentary. These assertions only
    # establish structural alignment with the official statements and answer.
    explanation_checks = {
        "explainA": ["ア", "6.5万円", "違反"],
        "explainB": ["イ", "各5万円", "違反しない"],
        "explainC": ["ウ", "3,400万円", "違反しない"],
        "explainD": ["ア、イ、ウ", "不正解"],
        "explainShort": ["イとウ", "ア", "違反"],
        "explainLong": ["イとウ", "ア", "違反"],
    }
    for field, needles in explanation_checks.items():
        if any(needle not in baseline[field] for needle in needles):
            raise AssertionError(f"{field} is not structurally aligned")

    proposed = dict(baseline)
    proposed["stem"] = OFFICIAL_STEM
    stem_lines = OFFICIAL_STEM.splitlines()
    statement_items = [
        {"label": line[0], "text": line[2:], "sha256": text_hash(line[2:]), "chars": len(line[2:])}
        for line in stem_lines[1:]
    ]

    full_payload = {
        "classification": "work_only_contains_official_question_text",
        "qId": QID,
        "status": "approved_restoration_specification_production_apply_requires_live_hash_preflight",
        "sources": {
            "archive_url": OFFICIAL_ARCHIVE_URL,
            "question_pdf_url": OFFICIAL_PDF_URL,
            "question_pdf_sha256": OFFICIAL_PDF_SHA256,
            "question_pdf_page_1based": 16,
            "question_printed_footer_visual": 14,
            "question_browser_page_index": 15,
            "question_page_image_sha256": OFFICIAL_PAGE_IMAGE_SHA256,
            "answer_pdf_url": OFFICIAL_PDF_URL,
            "answer_pdf_sha256": OFFICIAL_PDF_SHA256,
            "answer_pdf_page_1based": 29,
            "official_answer_number": OFFICIAL_CORRECT_NUMBER,
            "official_answer_key": OFFICIAL_CORRECT_KEY,
            "law_as_of": "2024-04-01",
        },
        "official_structure": {
            "prompt": stem_lines[0],
            "prompt_sha256": text_hash(stem_lines[0]),
            "statement_items": statement_items,
            "answer_options": {key: value for key, value in OFFICIAL_CHOICES.items()},
            "correct_number": OFFICIAL_CORRECT_NUMBER,
            "correct_key": OFFICIAL_CORRECT_KEY,
        },
        "old": {field: baseline.get(field, "") for field in FIELDS},
        "proposed": {field: proposed.get(field, "") for field in FIELDS},
        "explanation_assessment": {
            "result": "structurally_consistent_with_official_statements_and_answer",
            "limitation": "official source has no commentary; legal reasoning was not independently certified as official commentary",
        },
        "image_assessment": "official question has no figure/table; current image fields are empty",
        "live_state_assessment": {
            "direct_live_row_export": False,
            "evidence": "production v64 receipt records R6takken-028 as unchanged/protected exclusion; last deployment bundle preserves the before baseline",
            "local_canonical_import_state": local_state,
            "required_before_apply": "read current production row by qId and require exact old stem hash before any write",
        },
    }
    (WORK / "r6_q28_restoration_full_payload.json").write_text(
        json.dumps(full_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    field_rows = []
    for field in FIELDS:
        old = baseline.get(field, "")
        new = proposed.get(field, "")
        changed = old != new
        verification = "unchanged_and_matched"
        source = "current_three_way_match"
        if field == "stem":
            verification = "manual_transcription_from_hash_verified_official_page_image"
            source = "RETIO_official_question_pdf_page_16"
        elif field.startswith("choice") and field != "choiceImageUrl":
            verification = "matched_official_question_page"
            source = "RETIO_official_question_pdf_page_16"
        elif field == "correct":
            verification = "matched_official_answer_number_2_to_key_B"
            source = "RETIO_official_answer_table_page_29"
        elif field == "explainE":
            verification = "empty_preserved_no_fifth_option"
            source = "current_content_plus_official_four_option_structure"
        elif field.startswith("explain"):
            verification = "structurally_consistent_not_official_commentary"
            source = "current_content_plus_official_stem_and_answer"
        elif field in {"imageUrl", "choiceImageUrl"}:
            verification = "empty_and_official_page_has_no_figure"
            source = "RETIO_official_question_pdf_page_16"
        elif field == "source_ref":
            verification = "preserve_existing_record_provenance_official_evidence_is_in_release_ledger"
            source = "current_content_source_preserved"
        field_rows.append(
            {
                "qId": QID,
                "field": field,
                "action": "replace" if changed else "preserve",
                "old_value_redacted": redact_value(old),
                "new_value_redacted": redact_value(new),
                "old_sha256": text_hash(old),
                "new_sha256": text_hash(new),
                "old_chars": len(old),
                "new_chars": len(new),
                "verification": verification,
                "source": source,
                "official_question_url": OFFICIAL_PDF_URL,
                "official_question_pdf_sha256": OFFICIAL_PDF_SHA256,
                "official_question_page_1based": 16,
                "official_answer_url": OFFICIAL_PDF_URL,
                "official_answer_page_1based": 29,
                "official_answer_number": OFFICIAL_CORRECT_NUMBER,
                "official_answer_key": OFFICIAL_CORRECT_KEY,
                "applicable_law_as_of": "2024-04-01",
                "canonical_import_state": local_state,
                "deploy_bundle_state": "before",
                "direct_live_row_export": "false",
                "release_status": "approved_spec_pending_live_hash_preflight",
            }
        )
    ledger_path = WORK / "r6_q28_restoration_release_ledger.csv"
    with ledger_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(field_rows[0]))
        writer.writeheader()
        writer.writerows(field_rows)

    source_manifest = {
        "qId": QID,
        "official_archive_url": OFFICIAL_ARCHIVE_URL,
        "official_pdf_url": OFFICIAL_PDF_URL,
        "official_pdf_sha256": OFFICIAL_PDF_SHA256,
        "question_physical_page_1based": 16,
        "question_printed_footer_visual": 14,
        "question_browser_page_index_zero_based": 15,
        "question_page_image_sha256": OFFICIAL_PAGE_IMAGE_SHA256,
        "answer_physical_page_1based": 29,
        "answer_index": 28,
        "answer_number": OFFICIAL_CORRECT_NUMBER,
        "answer_key": OFFICIAL_CORRECT_KEY,
        "expected_label_sequence": [item["label"] for item in statement_items],
        "statement_sha256": {item["label"]: item["sha256"] for item in statement_items},
        "statement_chars": {item["label"]: item["chars"] for item in statement_items},
        "applicable_law_as_of": "2024-04-01",
        "later_law_change_note": (
            "RETIO archive warns that past questions may differ from current law. "
            "MLIT materials state the long-term-vacant-property remuneration exception took effect 2024-07-01."
        ),
        "mlit_change_source": "https://www.mlit.go.jp/tochi_fudousan_kensetsugyo/const/content/001750145.pdf",
        "transcription_method": "manual_from_hash_verified_official_page_image; PDF_text_layer_not_used_as_character_oracle",
        "input_row_sources": {name: str(path) for name, path in INPUTS.items()},
        "input_row_states": {"canonical": local_state, "import": local_state, "last_deploy_bundle": "before"},
        "production_receipt": str(PRODUCTION_RECEIPT),
        "direct_live_row_export": False,
    }
    (WORK / "r6_q28_restoration_source_manifest.json").write_text(
        json.dumps(source_manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    changed_fields = [row["field"] for row in field_rows if row["action"] == "replace"]
    summary = f"""# R6takken-028 公式原典復元監査（redacted）

## 結論

- 復元仕様: **承認可**。公式問題・公式正答とも同一RETIO公式PDFで確認済み。
- 本番適用: **未承認**。本監査では本番QuestionBank行を直接exportしていないため、適用直前にqIdと旧stem hashを一致確認するread-only preflightが必要。
- 変更対象フィールド: `{', '.join(changed_fields)}` のみ。
- そのほかの選択肢、正答、解説、画像参照、statusは保存する。
- ローカルcanonical/import状態: `{local_state}`。last deployment bundleはbefore証跡として保持。

## 公式照合

- 問題: RETIO公式PDFの物理16ページ目（ブラウザpage index 15、画像上の印刷ページ表記14）。項目はア・イ・ウの3件、順序固定。
- 選択肢: 1〜4の組合せをA〜Dへ対応させた現行値は全件一致。
- 正答: 公式正解表の問28は2、現行key Bと一致。
- 図表: 公式問題に図表なし。現行の画像参照も空。
- 解説: 公式解説は存在しない。現行解説は項目・数値・正誤結論の構造整合のみ確認し、公式解説としての認定はしていない。

## 現行欠落・混入

- stemから公式のア・イ・ウ本文が3件とも欠落。
- stem末尾に、公式試験後の制度変更を意識した長期空家等の条件文が混入しているが、公式原文には存在しない。
- source_refは第三者サイトだが、現行解説の出典でもあり得るため変更しない。公式問題・正答の証跡はrelease ledger/source manifestに分離して保持する。

## 法改正注意

- 本問は公式に2024-04-01施行法令基準。
- RETIO公式アーカイブは、法改正により現在法と一致しない場合があると注意喚起。
- 国土交通省資料では長期の空家等に関する報酬特例は2024-07-01施行。問題本文を現在法へ書き換えず、令和6年度過去問として基準日を明示する。

## 公開ゲート

1. 本番行をqIdでread-only取得する。
2. 旧stem hash `{text_hash(baseline['stem'])}` と、選択肢・正答・解説・画像の不変条件を照合する。
3. 一致した場合だけ、stemの1フィールドを更新する。
4. 更新後にア・イ・ウの3行表示、選択肢4件、正答Bをread-backし、非対象フィールドhash不変を確認する。
"""
    (WORK / "r6_q28_restoration_summary.md").write_text(summary, encoding="utf-8")

    print(
        json.dumps(
            {
                "qId": QID,
                "officialAnswer": OFFICIAL_CORRECT_NUMBER,
                "currentCorrect": baseline["correct"],
                "changedFields": changed_fields,
                "approvedSpecification": True,
                "productionApply": "blocked_pending_direct_live_hash_preflight",
                "ledgerRows": len(field_rows),
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
