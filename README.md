# takken-training

宅地建物取引士（宅建）試験 過去問演習アプリ（H28-R7、600問）GAS + Spreadsheet DB

## 概要
- 技術構成: Google Apps Script Web アプリ + Google Sheets DB
- 問題数: 600問（H28〜R7）
- ベース: sekisan-training フォーク

## データ
- `data/takken_all_final.csv`: 600問統合済み

## セットアップ
1. `npm install`
2. `npx clasp login`
3. `npx clasp create --title "takken-training" --type standalone`
4. `npx clasp push`
5. GASエディタで `setup_()` を実行
