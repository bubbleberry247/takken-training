# QuestionBank CSVインポート機能

## 概要

Google Apps Script に CSVインポート機能を実装しました。約682問のQuestionBankデータをCSVファイルから一括インポートできます。

## 実装内容

### 新規ファイル

- **`src/importCsv.gs`**: CSVインポート機能の実装
  - `importQuestionBankFromCsv(csvText)`: CSVテキストを受け取りQuestionBankシートにインポート
  - `importQuestionBankFromFolder()`: Google Driveフォルダから自動インポート
  - `importQuestionBankFromDriveFile(fileId)`: DriveファイルIDを指定してインポート
  - `getQuestionBankImportUrl()`: インポート用フォルダURLを取得
  - `testImportQuestionBankFromCsv()`: サンプルデータでテスト実行
  - `parseCsv_()`: CSVパーサー（ダブルクォート、エスケープ対応）
  - `parseCsvLine_()`: CSV行パーサー

### Code.gs の更新

以下のエンドポイントを追加:

- `?action=importCsvFromFolder`: フォルダからインポート実行
- `?action=getImportFolderUrl`: フォルダURL取得
- `POST { action: 'importCsvText', csvText: '...' }`: CSVテキストを直接インポート

## 使用方法

### 推奨: Google Drive 経由でインポート

1. **Apps Script エディタを開く**
   ```
   https://script.google.com/home/projects/1giv21Jbc8lSmC8fQ3TDJ6gNP7-nH2m2KnPAYebhd0rK8B65gc0mvFzKS/edit
   ```

2. **フォルダURLを取得**
   - `importCsv.gs` または `Code.gs` を開く
   - 関数: `getQuestionBankImportUrl` を実行
   - 実行ログに表示されるフォルダURLをコピー

3. **CSVファイルをアップロード**
   - フォルダURLをブラウザで開く
   - `tools/questionbank_drive_import.csv` をアップロード
   - ファイル名を **`questionbank_import.csv`** にリネーム（重要）

4. **インポート実行**
   - Apps Script エディタに戻る
   - 関数: `importQuestionBankFromFolder` を実行
   - 実行ログで結果を確認

5. **確認**
   - DB Spreadsheet を開く: https://docs.google.com/spreadsheets/d/1jj3AgZR2jAbgUIPtFRtjSfO0R0u5K_fiZyYQMwhEbM0/edit
   - QuestionBankシートを確認
   - 期待: 685行（ヘッダー1行 + データ684行）

### 代替: サンプルデータでテスト

Apps Script エディタで以下を実行:

```javascript
testImportQuestionBankFromCsv()
```

サンプル3行のみインポートされます。

## CSVファイル仕様

- **ファイル**: `tools/questionbank_drive_import.csv`
- **サイズ**: 約280KB
- **行数**: 685行（ヘッダー1 + データ684）
- **列数**: 30列
- **エンコーディング**: UTF-8（BOMなし）
- **フォーマット**:
  - カンマ区切り
  - ダブルクォートでフィールドをエスケープ
  - フィールド内のダブルクォートは `""` でエスケープ

### ヘッダー

```
qId,segmentId,type,difficulty,tag1,tag2,tag3,lawTag,revisionFlag,conceptId,variantGroupId,source_ref,imageUrl,choiceImageUrl,stem,choiceA,choiceB,choiceC,choiceD,choiceE,explainA,explainB,explainC,explainD,explainE,correct,explainShort,explainLong,status,updatedAt
```

## エラーハンドリング

### よくあるエラー

| エラーメッセージ | 原因 | 解決方法 |
|----------------|------|----------|
| `questionbank_import.csv not found in folder` | ファイル名が違う | ファイル名を `questionbank_import.csv` に変更 |
| `CSV contains too many rows (limit: 10000)` | CSVが大きすぎる | 分割してインポート（現在は684行なので問題なし） |
| `CSV contains no data` | CSVが空 | CSVファイルの内容を確認 |
| `Exception: シートが見つかりません: QuestionBank` | DBが未設定 | `setup()` を実行してDBを作成 |

### Apps Script実行時間制限

- **制限**: 6分
- **現在の処理時間**: 約1分未満（684行）
- **対策**: 6分を超える場合はCSVを分割

## 技術詳細

### CSVパーサーの特徴

- ダブルクォート対応（RFC 4180準拠）
- エスケープ対応（`""`）
- BOM除去（UTF-8 BOM対応）
- 改行対応（`\r\n`, `\n`, `\r`）

### パフォーマンス

- **一括書き込み**: `sheet.getRange().setValues()` で高速化
- **キャッシュクリア**: インポート後に自動的にキャッシュをクリア

### セキュリティ

- Google Drive経由の方法はGoogle認証が必要（安全）
- Web API経由の方法は認証設定次第（現在は401エラー）

## テストツール

### ローカルツール

- **`test_csv_parser.py`**: CSV構造のテスト
- **`prepare_csv_for_paste.py`**: エディタ貼り付け用エスケープ
- **`import_csv.py`**: Web API経由インポート（認証設定変更が必要）

実行例:

```bash
cd tools
python test_csv_parser.py
```

## トラブルシューティング

### 列数の不一致について

test_csv_parser.py を実行すると、列数がばらついているように見えますが、これはダブルクォート内のカンマをカウントしているためです。Apps Scriptの `parseCsv_()` は正しく処理します。

### multiline fields について

一部の行でダブルクォートが複数行にまたがる可能性がありますが、現在のCSVには該当データがないことを確認済みです（test結果で483-484行目の警告は誤検知）。

## 今後の拡張

- [ ] CSVエクスポート機能
- [ ] 差分インポート（既存データとマージ）
- [ ] バリデーション機能（インポート前のデータ検証）
- [ ] 進捗表示（大量データ対応）

## 関連ファイル

- `src/importCsv.gs`: 実装
- `src/Code.gs`: エンドポイント追加
- `tools/questionbank_drive_import.csv`: CSVデータ
- `tools/IMPORT_INSTRUCTIONS.md`: 詳細手順
- `tools/test_csv_parser.py`: テストツール

## 更新履歴

- 2026-02-16: 初版作成（CSVインポート機能実装）
