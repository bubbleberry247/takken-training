# AI Handoff (sekisan-training)

最終更新: `2026-04-11`

目的: 建築積算士 一次試験向けの `sekisan-training` を、`GAS + Spreadsheet + HtmlService` の独立 Web アプリとして運用再開できる状態にそろえる。

## 主要情報
- リポジトリ: `C:\ProgramData\Generative AI\Github\sekisan-training`
- GAS Script ID: `1_REQ7n8e4xJkX1E3nqseFvwivdTErh2JpaJ9Rhp06dxshravzgoFOqub`
- 最新記録 deployment ID: `AKfycbyFJ45I-JQHW7U1s5ON9S2iNA23QLjvPt4AOclEx-bI1AMXsM0GuDpSZPorj73fVRhg`
- 想定 exec URL: `https://script.google.com/macros/s/AKfycbyFJ45I-JQHW7U1s5ON9S2iNA23QLjvPt4AOclEx-bI1AMXsM0GuDpSZPorj73fVRhg/exec`
- localStorage prefix: `sekisanTraining_`
- アプリ名: `建築積算士 一次試験 過去問演習`

## この時点で完了していること
- `sekisan-training` は別アプリとして Script ID を分離済み
- manifest / README / `CLAUDE.md` / 各種 GAS ソースは sekisan 用に切替済み
- 完成版データを repo に配置済み:
  - `data/sekisan_all_final.csv`
  - `data/sekisan_all_final_report.json`
- 画像 108 枚を `images/sekisan/` に配置済み
- ホーム画面のデザイン方針は `MUJI` に決定
- `src/index.html` は MUJI 方向で再調整済み
- ローカル確認用に `google.script.run` 非依存の fallback を追加済み
- デザイン比較・参照用の静的ページを追加済み:
  - `docs/design-comparison.html`
  - `docs/japanese-design-skill-catalog.html`

## 未完了 / いまのブロッカー
- DB 初期化がまだ
- そのため Web アプリでは `DBが未設定です。setup_()を実行してください。` が表示される
- 実際に呼ぶべき関数は `src/db.gs` の `setup()`。再作成時は `setupForce()`
- `clasp run setup` は権限処理で詰まったため、Apps Script エディタからの実行を優先する
- DB がないので、`QuestionBank` への CSV 投入と Drive 画像リンクも未完了

## 再開手順
1. `C:\ProgramData\Generative AI\Github\sekisan-training` で `npm install`
2. `npx clasp push`
3. Apps Script エディタで `setup()` を実行
4. Script Properties に `DB_SPREADSHEET_ID` が保存されたことを確認
5. Admin 画面の Dry-run -> Import で `data/sekisan_all_final.csv` を投入
6. `images/sekisan/` を Drive フォルダにアップロード
7. UI から `apiAdminLinkAllDriveImages` を実行して `imageUrl` を実 URL 化
8. 必要なら再 deploy

## デザインまわり
- ユーザー選択: `muji`
- 狙い:
  - 紙っぽい白 / きなり基調
  - 赤は `MUJI Red` を最小限に使用
  - フラットな境界線ベース
  - 強い影、派手なグラデーション、大きい角丸は使わない
- 主な変更点:
  - ヘッダ / ヒーロー / ホームカード群を MUJI トーンへ再調整
  - serif 寄りから、素朴な sans-serif 中心へ寄せ直し
  - ローカルプレビュー時は `ローカルプレビュー中: Apps Script 連携なし` を表示

## ローカル確認方法
- アプリ画面:
  - `C:\ProgramData\Generative AI\Github\sekisan-training\src` で `python -m http.server 8765`
  - `http://127.0.0.1:8765/index.html`
- 参考ページ:
  - repo root で `python -m http.server 8766`
  - `http://127.0.0.1:8766/docs/design-comparison.html`
  - `http://127.0.0.1:8766/docs/japanese-design-skill-catalog.html`

## 重要ファイル
- `src/db.gs`: DB 初期化、`setup()` / `setupForce()`
- `src/api.gs`: API と Drive 画像リンク
- `src/Code.gs`: `doGet`、診断アクション
- `src/sekisanConfig.gs`: アプリ設定、年度・画像名変換
- `src/index.html`: MUJI デザイン調整とローカルプレビュー fallback
- `data/sekisan_all_final.csv`: 本番投入用の完成版 CSV
- `data/sekisan_all_final_report.json`: 検証レポート

## 次にやるとよいこと
- まず DB 初期化を終わらせる
- その後に CSV インポートと画像リンクを完了する
- 必要なら MUJI トーンを模試画面 / 結果画面にも追加で広げる
