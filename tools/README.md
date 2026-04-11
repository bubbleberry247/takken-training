# tools/ — データ整備・管理スクリプト

QuestionBank CSV の作成・検証・インポートに使った Python スクリプト群。
主に初期データ整備フェーズ（2026年2月）に使用。現在は大部分がアーカイブ状態。

[← リポジトリルートへ](../README.md)

## 現在も使用するスクリプト

| スクリプト | 用途 |
|-----------|------|
| `generate_testplan14.py` | TestPlan14 CSV を生成する |
| `import_csv.py` | QuestionBank CSV を GAS DB へインポート |
| `validate_csv_integrity.py` | CSV のスキーマ・整合性チェック |
| `check_integrity.py` | 問題データの整合性確認 |
| `check_quality.py` | QuestionBank 品質チェック（欠損・形式） |
| `tag_questions.py` | 問題に tag1/tag2/tag3 を付与する |
| `tag_statistics.py` | タグ別問題数の集計 |
| `populate_image_urls.py` | 画像 URL を QuestionBank に投入 |
| `add_choice_image_url.py` | 選択肢画像 URL を投入 |
| `auto_update_sheets.py` | Google Sheets へ自動更新 |
| `upload_csv_to_drive.py` | CSV を Google Drive へアップロード |

## データ抽出・変換スクリプト

Word/PDF から問題テキストを抽出・変換するスクリプト群（初期データ整備時に使用）。

| スクリプト | 用途 |
|-----------|------|
| `extract_old_format_r1_r3.py` | R1〜R3 旧フォーマット問題の抽出 |
| `extract_middle_format_r4_r5.py` | R4〜R5 中間フォーマット問題の抽出 |
| `extract_new_format_r7.py` | R7 新フォーマット問題の抽出 |
| `extract_r6_explanations.py` | R6 解説テキストの抽出 |
| `extract_explanations_from_docx.py` | Word ファイルから解説を抽出 |
| `extract_question_images.py` | 問題画像を PDF/Word から抽出 |
| `parse_questions.py` | 問題テキストのパース処理 |
| `convert_to_questionbank.py` | 各種フォーマットを QuestionBank 形式に変換 |

## 修正・クリーニングスクリプト

OCR エラー修正、フォーマット統一などに使用したスクリプト群。

| スクリプト | 用途 |
|-----------|------|
| `apply_ocr_fixes.py` / `apply_ocr_fixes_v2.py` | OCR 誤認識の一括修正 |
| `fix_format_issues.py` | フォーマット統一 |
| `fix_fill_in_blanks.py` | 穴埋め問題の形式修正 |
| `fix_stem_format.py` / `fix_stem_formatting.py` | 問題文フォーマット修正 |
| `fix_choice_duplicates.py` | 選択肢重複の修正 |
| `clean_explanations.py` | 解説テキストのクリーニング |
| `clean_furigana.py` | ふりがな除去 |
| `normalize_choice_numbers.py` | 選択肢番号の正規化 |
| `merge_explanations.py` | 複数ソースからの解説テキストをマージ |

## 検証・レポートスクリプト

| スクリプト | 用途 |
|-----------|------|
| `check_missing_explanations.py` | 解説が未入力の問題を検出 |
| `check_image_questions.py` | 画像付き問題の確認 |
| `check_r3_status.py` | R3 問題のインポート状況確認 |
| `analyze_explanation_gaps.py` | 解説の欠損パターン分析 |
| `detect_ocr_errors.py` | OCR エラーの検出 |
| `format_analysis_report.py` | フォーマット検証レポート生成 |
| `generate_summary_report.py` | 全体サマリーレポート生成 |

## 主要データファイル

<!-- AUTO-GENERATED: do not edit manually -->
| ファイル | 内容 |
|----------|------|
| `questionbank.csv` | QuestionBank 作業中 CSV |
| `questionbank_complete.csv` | QuestionBank 完成版 CSV |
| `questionbank_drive_import.csv` | Google Drive インポート用 CSV（最新正本） |
| `questionbank_drive_import_final.csv` | Drive インポート最終確定版 |
| `testplan14.csv` | TestPlan14 定義 CSV |
| `all_questions.json` | 全問題 JSON 形式 |
| `user_access_import.csv` | UserAccess 一括インポート用 CSV |
| `image_mapping.csv` | 問題 ID と画像ファイルのマッピング |
| `missing_explanations.csv` | 解説未入力問題リスト |
| `fix_manual_list.csv` | 手動修正が必要な問題リスト |
<!-- END AUTO-GENERATED -->

## レポートファイル

データ整備作業で生成されたレポート。参照専用（編集不要）。

- `DATA_VALIDATION_README.md` — データ検証手順の説明
- `FORMAT_CHECK_SUMMARY.md` / `FORMAT_CHECK_FINAL_REPORT.md` — フォーマット検証結果
- `OCR_FIX_SUMMARY.md` / `OCR_FIX_FINAL_REPORT.md` — OCR 修正作業の結果報告
- `IMPORT_INSTRUCTIONS.md` — CSV インポート手順
- `PARSER_EXTRACTION_REPORT.md` — 抽出処理の結果報告
- `分数数式検証レポート_2026-02-16.md` — 数式表記の検証結果

## バックアップファイルについて

`questionbank_drive_import_backup_YYYYMMDD_HHmmss.csv` は作業履歴として保存されたもので、
通常の開発作業では参照不要。正本は `questionbank_drive_import_final.csv`。

## 注意事項

- `__pycache__/` は Python の自動生成ディレクトリ。コミット不要（`.gitignore` 対象）。
- 各スクリプトは `data/` フォルダの CSV を参照する場合がある。実行前に `data/` のファイルを確認すること。
- GAS への書き込みを行うスクリプト（`upload_csv_to_drive.py` 等）は、本番実行前に Dry-run オプションで動作確認すること。
