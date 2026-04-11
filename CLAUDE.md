# sekisan-training

建築積算士 一次試験の過去問演習アプリ。`Google Apps Script + Spreadsheet + HtmlService` の独立 Web アプリとして `sekisan-training` 専用の Script ID / deployment を使う。

## 現在の状態
- GAS Script ID: `1_REQ7n8e4xJkX1E3nqseFvwivdTErh2JpaJ9Rhp06dxshravzgoFOqub`
- 最新記録 deployment ID: `AKfycbyFJ45I-JQHW7U1s5ON9S2iNA23QLjvPt4AOclEx-bI1AMXsM0GuDpSZPorj73fVRhg`
- `localStorage` prefix: `sekisanTraining_`
- App title: `建築積算士 一次試験 過去問演習`
- 学習プラン: 12 テスト
- 年度: `H25` から `R7`
- セグメント: `sekisan_I` / `sekisan_II`
- 完成版データは repo 反映済み:
  - `data/sekisan_all_final.csv`
  - `data/sekisan_all_final_report.json`
- 画像 108 枚は `images/sekisan/` に配置済み
- ホーム画面は 2026-04-11 に `MUJI` 方向で再調整済み
- `src/index.html` にはローカルプレビュー fallback を追加済み

## いまのブロッカー
- DB 未初期化のため、Web アプリでは `DBが未設定です。setup_()を実行してください。` が出る
- 実際の公開入口は `src/db.gs` の `setup()` と `setupForce()`
- `clasp run setup` では権限処理が通らなかったため、Apps Script エディタから `setup()` を実行するのが最短

## 再開手順
```bash
npm install
npx clasp push
```

1. Apps Script エディタで `setup()` を実行
2. Script Properties に `DB_SPREADSHEET_ID` が保存されたことを確認
3. Admin 画面の Dry-run -> Import で `data/sekisan_all_final.csv` を投入
4. `images/sekisan/` を Drive にアップロード
5. UI から `apiAdminLinkAllDriveImages` を実行して `imageUrl` を Drive URL に更新
6. 必要なら再 deploy

## プレビュー / 参考ページ
- ホーム画面プレビュー: `http://127.0.0.1:8765/index.html`
- デザイン比較: `http://127.0.0.1:8766/docs/design-comparison.html`
- 日本サイト参照カタログ: `http://127.0.0.1:8766/docs/japanese-design-skill-catalog.html`
- 参考ファイル:
  - `docs/design-comparison.html`
  - `docs/japanese-design-skill-catalog.html`
  - `docs/ai_handoff.md`

## 重要ファイル
- `src/sekisanConfig.gs`: アプリ定数、年度表示、画像ファイル名変換
- `src/db.gs`: シート初期化、`setup()` / `setupForce()`
- `src/api.gs`: Home/Test/Mock API と画像リンク処理
- `src/Code.gs`: `doGet`, 診断アクション、補助ユーティリティ
- `src/index.html`: UI 全体。MUJI 方向の調整とローカルプレビュー fallback を含む

## 運用メモ
- QuestionBank の画像付き問題は CSV 上では `images/sekisan/sekisan_H25_043.png` のようなプレースホルダを持つ
- Drive にアップロードする画像ファイル名も `sekisan_<年度>_<問題番号>.png` 形式で揃える
- GitHub raw を使う場合は Script Properties の `SEKISAN_GITHUB_IMAGE_BASE_URL` で上書き可能
