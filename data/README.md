# data/ — 問題データ（CSV）

QuestionBank に投入する問題データを格納するフォルダ。

[← リポジトリルートへ](../README.md)

## ファイル一覧

<!-- AUTO-GENERATED: do not edit manually -->
| ファイル | 内容 |
|----------|------|
| `explanations.csv` | 解説テキスト（正本、最新版） |
| `explanations_complete.csv` | 解説テキスト（全問完全版） |
| `explanations_backup_20260216_093148.csv` | 解説バックアップ（2026-02-16 09:31） |
| `explanations_backup_20260216_093203.csv` | 解説バックアップ（2026-02-16 09:32） |
| `sekisan_all_final.csv` | 建築積算士 QuestionBank 完成版（650問） |
| `sekisan_all_final_report.json` | 完成版 CSV の検証レポート |
<!-- END AUTO-GENERATED -->

## 注意事項

- CSV の列ヘッダ正本は `src/db.gs` の `HEADERS[SHEETS.QuestionBank]` です。
- 本番 DB へのインポートは Admin 画面から Dry-run を実行してから本番 Import を行うこと。
- バックアップファイルは直接 DB に取り込まないこと（最新の `explanations.csv` または `explanations_complete.csv` を使う）。
- sekisan アプリに投入する主データは `sekisan_all_final.csv` を使用すること。
