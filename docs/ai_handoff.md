# AI Handoff (takken-training)

最終更新: `2026-06-19`

目的: 宅地建物取引士（宅建）試験向けの `takken-training` を、`GAS + Spreadsheet + HtmlService` の独立 Web アプリとして公開できる状態にそろえる。

## 主要情報
- リポジトリ: `C:\ProgramData\Generative AI\Github\takken-training`
- アプリ名: `宅地建物取引士（宅建）過去問演習`
- localStorage prefix: `takkenTraining_`
- データ: H28〜R7、R2/R3の追加回を含む600問
- 正規化済み投入CSV: `data/takken_questionbank_import.csv`
- 生成コマンド: `python tools/build_takken_import_csv.py`
- 公開 deployment ID: `AKfycbyYREY2qC9lp6-KPlQNbIo5f1fsyKxnGPVceUTs7kQmiS0Zk2CZbSlKEabrkKhXMz6eDw`
- 公開 exec URL: `https://script.google.com/macros/s/AKfycbyYREY2qC9lp6-KPlQNbIo5f1fsyKxnGPVceUTs7kQmiS0Zk2CZbSlKEabrkKhXMz6eDw/exec`

## 完了していること
- `takken-training` は独立 Script ID を持つ
- UI は宅建表記へ切替済み
- QuestionBank投入用CSVを `published` / `knowledge` / 宅建4分野へ正規化済み
- R2/R3 の追加回を `R2A` / `R2B`、`R3A` / `R3B` として扱う
- 出題ロジック、模試 qId 解析、分野別統計、TestPlan14 を宅建用へ更新済み
- 2026-06-17: 既存公開デプロイを @11 に更新済み
- 2026-06-17: `QuestionBank` に600問投入済み、`TestPlan14` 再作成済み
- 2026-06-17: 診断で `totalQB=600`, `published=600`, `valid=600` を確認済み
- 2026-06-17: 年度別模試は H28/H29/H30/R1/R2A/R2B/R3A/R3B/R4/R5/R6/R7 各50問を確認済み
- 2026-06-17: Playwright実ブラウザ確認済み。初期表示、概要開閉、スマホ表示、手動ログイン後の開始・選択肢クリック・解答表示はOK。ログイン状態リセットの空iframe不具合を修正し @8 にデプロイ済み。
- 2026-06-17: 管理者/上長ダッシュボードを `showInDashboard` ベースへ更新し、管理画面からユーザーCSV一括登録できるようにした。土木・建築と同じ26名を `UserAccess` に同期済み。
- 2026-06-17: スクロールトップボタンを 44px 固定・初期非表示へ修正し @11 にデプロイ済み。
- 2026-06-19: 公開デプロイを @20 に更新。Playwrightで Login / Google認可画面への遷移 / Home / Dashboard / Admin / Test開始 / Mobile を確認し、`pageErrors: []`。
- 2026-06-19: Configシートの `GOOGLE_CLIENT_ID` と Script Properties の `GOOGLE_CLIENT_SECRET` を設定済み。Google Cloud側OAuth clientに宅建士の公開exec URLを redirect URI として登録済み。
- 2026-06-19: GISボタン方式は検証したが、Apps Script HtmlService が `script.googleusercontent.com` iframe originで動くため、Google側で `origin is not allowed` となる。公開版は建築/土木と同じサーバーOAuth方式のまま維持。

## 再確認ポイント
1. `npx clasp push`
2. 必要なら `?action=resetTestPlan` で TestPlan14 を宅建用に再作成
3. `data/takken_questionbank_import.csv` を QuestionBank に投入
4. `?action=diagTestGen&testIndex=1` で `totalQB=600`、`segMatch>0` を確認
5. `?action=diagMock` で R2A/R2B/R3A/R3B/R7 などの年度別件数を確認
6. OAuthログインは有効化済み。`?diag=oauth` で `GOOGLE_CLIENT_ID=SET`、`GOOGLE_CLIENT_SECRET=SET`、`URL_MATCH=OK`、`CLIENT_ID_FORMAT=OK (IAM OAuth client UUID)` を確認する。
7. `node output/playwright/verify_takken_prod.js` で本番確認する。2026-06-19時点の最新結果は `verify-takken-prod-2026-06-19T02-58-13-255Z.json`、`oauthConfigured=true` / `googleAuthReached=true` / `pageErrors=[]`。

## 注意
- 元データ `data/takken_all_final.csv` は直接インポートしない。`active` / `4choice` / 空 `segmentId` が含まれるため、アプリの出題条件に合わない。
- 本番投入は `data/takken_questionbank_import.csv` を使う。
