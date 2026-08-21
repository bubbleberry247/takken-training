# data/ — 問題データ（CSV）

QuestionBank に投入する問題データを格納するフォルダ。

[← リポジトリルートへ](../README.md)

## ファイル一覧

<!-- AUTO-GENERATED: do not edit manually -->
| ファイル | 内容 |
|----------|------|
| `takken_all_final.csv` | 宅建過去問の元データ（600問） |
| `takken_questionbank_import.csv` | QuestionBank 投入用の正規化済み CSV |
| `statement_label_corrections.csv` | 公式原典照合済み51問のstemラベル修正台帳（R6takken-028/Q38除外） |
| `r6_takken_028_release_ledger.csv` | R6問28専用の公式原典release台帳（approved・stem 1列のみ） |
<!-- END AUTO-GENERATED -->

## 注意事項

- CSV の列ヘッダ正本は `src/db.gs` の `HEADERS[SHEETS.QuestionBank]` です。
- 本番 DB へのインポートは Admin 画面から Dry-run を実行してから本番 Import を行うこと。
- バックアップファイルは直接 DB に取り込まないこと（最新の `explanations.csv` または `explanations_complete.csv` を使う）。
- 宅建アプリに投入する主データは `takken_questionbank_import.csv` を使用すること。
- `takken_questionbank_import.csv` は `python tools/build_takken_import_csv.py` で再生成すること。
- R6問28は公式原典監査でstemのみapproved。選択肢・正答・解説・画像・source_ref・statusは保護し、本番はliveのbefore全行hash一致後に局所patchで反映すること。
