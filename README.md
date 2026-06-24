# takken-training

宅地建物取引士（宅建）試験 過去問演習アプリ（H28-R7、600問）GAS + Spreadsheet DB

## 概要
- 技術構成: Google Apps Script Web アプリ + Google Sheets DB
- 問題数: 600問（H28〜R7）
- ベース: sekisan-training フォーク
- 公開URL: https://script.google.com/macros/s/AKfycbyYREY2qC9lp6-KPlQNbIo5f1fsyKxnGPVceUTs7kQmiS0Zk2CZbSlKEabrkKhXMz6eDw/exec
- 2026-06-17: 600問投入、TestPlan14再作成、公開デプロイ @8 で診断済み
- 2026-06-17: 公開デプロイ @11 に更新。管理者/上長ダッシュボード用 `UserAccess.showInDashboard`、ユーザーCSV一括登録、土木・建築と同じ26名のUserAccess同期、スクロールトップ44px化を反映。
- 2026-06-17: Playwright実ブラウザ確認済み。初期表示、概要開閉、手動ログイン後の開始・選択肢クリック・解答表示、スマホ表示はOK。OAuthログインは後続の @20 で有効化済み。
- 2026-06-19: 公開デプロイ @20 に更新。Home / Dashboard / Admin / Test開始 / Mobile は Playwright 確認OK。OAuthログインは `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` / Google Cloud redirect URI 設定済みで、Google認可画面への遷移まで確認済み。

## データ
- `data/takken_all_final.csv`: 600問統合済み
- `data/takken_questionbank_import.csv`: QuestionBank投入用に正規化済み
- 生成: `python tools/build_takken_import_csv.py`

## セットアップ
1. `npm install`
2. `npx clasp login`
3. `npx clasp create --title "takken-training" --type standalone`
4. `npx clasp push`
5. GASエディタで `setup_()` を実行
6. `data/takken_questionbank_import.csv` を QuestionBank にインポート

## 公開確認
- `diagTestGen`: `totalQB=600`, `published=600`, `valid=600`
- `diagMock`: H28/H29/H30/R1/R2A/R2B/R3A/R3B/R4/R5/R6/R7 各50問
- 公開ページタイトル: `宅建 過去問演習`
- `verify_takken_prod.js`: `pageErrors: []`, `oauthConfigured=true`, 週テスト12件、年度別模試12件、Dashboard 24名、Admin 26名、テスト開始/選択肢クリックOK
