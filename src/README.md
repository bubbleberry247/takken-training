# src/ — GAS ソースコード

宅地建物取引士（宅建）向けアプリの GAS 実装ファイル群です。

[← リポジトリルートへ](../README.md)

## 役割
- `Code.gs`: `doGet` と診断用アクション
- `db.gs`: シート定義、`setup_()`, `TestPlan14` 初期化
- `logic.gs`: 出題ロジック、採点、統計、アドバイス生成
- `api.gs`: Home/Test/Mock/Admin API
- `auth.gs`: OAuth とユーザー識別
- `index.html`: 単一 HTML のフロントエンド
- `importCsv.gs`: Dry-run / Import の CSV 取り込み
- `sekisanConfig.gs`: sekisan 固有の年度、表示名、画像パス変換

## シート一覧
- `Config`
- `Users`
- `QuestionBank`
- `UserAccess`
- `TestPlan14`
- `TestSets`
- `Attempts`
- `AttemptAnswers`
- `TagStats`

## takken 固有メモ
- `QuestionBank.segmentId` は `takken_rights` / `takken_law` / `takken_business` / `takken_other`
- 模試の `testIndex` は `H28takken` / `R2Atakken` / `R7takken` 形式
- R2/R3 は追加回を含むため `R2A` / `R2B`、`R3A` / `R3B` として扱う
- 画像ファイル名を使う場合は `takken_<年度>_<問題番号>.png`
