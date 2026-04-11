# src/ — GAS ソースコード

建築積算士 一次試験向けアプリの GAS 実装ファイル群です。

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

## sekisan 固有メモ
- `QuestionBank.segmentId` は `sekisan_I` または `sekisan_II`
- 模試の `testIndex` は `H25sekisan` / `R7sekisan` 形式
- 画像ファイル名は `sekisan_<年度>_<問題番号>.png`
- 画像付き問題の CSV プレースホルダは `images/sekisan/...`
