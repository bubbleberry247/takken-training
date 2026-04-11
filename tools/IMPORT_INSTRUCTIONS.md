# QuestionBank CSVインポート手順

## 方法1: Google Drive 経由（推奨）

### 手順

1. **Google Driveフォルダを準備**
   - Apps Script エディタを開く: https://script.google.com/home/projects/1giv21Jbc8lSmC8fQ3TDJ6gNP7-nH2m2KnPAYebhd0rK8B65gc0mvFzKS/edit
   - `Code.gs` または `importCsv.gs` を開く
   - 以下の関数を実行: `getQuestionBankImportUrl`
   - 実行ログに表示されるフォルダURLをコピー

2. **CSVファイルをアップロード**
   - フォルダURLをブラウザで開く
   - `tools/questionbank_drive_import.csv` をフォルダにアップロード
   - ファイル名を `questionbank_import.csv` にリネーム（重要）

3. **インポートを実行**
   - Apps Script エディタで `importQuestionBankFromFolder` を実行
   - 実行ログを確認してインポート結果を確認

### エラーハンドリング

- **エラー: "questionbank_import.csv not found in folder"**
  - ファイル名が正しいか確認（`questionbank_import.csv`）
  - フォルダに複数の同名ファイルがある場合、最新のものが使用されます

- **エラー: "CSV contains too many rows (limit: 10000)"**
  - CSVファイルが10000行を超えている場合、分割してインポート

---

## 方法2: Apps Script エディタで直接実行（サンプルデータのみ）

Apps Script エディタで以下の関数を実行すると、サンプルデータ（3行）がインポートされます:

```javascript
function testImportQuestionBankFromCsv() {
  // 実装済み（importCsv.gs）
}
```

---

## 方法3: Web API 経由（デプロイ設定が必要）

現在、Web アプリのデプロイ設定が「認証が必要」になっているため、POSTリクエストは401エラーになります。

### デプロイ設定を変更する場合

1. Apps Script エディタ右上の「デプロイ」→「デプロイを管理」
2. 既存のデプロイを編集
3. 「次のユーザーとして実行」: 自分
4. 「アクセスできるユーザー」: **全員** に変更
5. 保存

変更後、以下のPythonスクリプトが使用可能になります:

```bash
cd tools
python import_csv.py
```

---

## 確認方法

インポート後、Google Sheetsを開いて確認:

- DB Spreadsheet: https://docs.google.com/spreadsheets/d/1jj3AgZR2jAbgUIPtFRtjSfO0R0u5K_fiZyYQMwhEbM0/edit
- QuestionBankシートを開く
- 行数を確認（ヘッダー含めて685行になるはず）

---

## トラブルシューティング

### Apps Script実行時間制限（6分）

682問のCSVインポートは通常1分以内に完了しますが、もし6分を超える場合:

1. CSVを分割（例: 300行ずつ）
2. 各ファイルを順番にインポート

### メモリ不足エラー

Apps Scriptのメモリ制限（約100MB）を超える場合:

- CSVファイルサイズを確認（現在約280KB）
- explainLong列など大きなテキストがある場合、一時的に削除

---

## 実装詳細

### 新規ファイル

- `src/importCsv.gs`: CSVインポート機能の実装

### 追加された関数

- `importQuestionBankFromCsv(csvText)`: CSVテキストをインポート
- `importQuestionBankFromFolder()`: Google Driveフォルダから自動インポート
- `importQuestionBankFromDriveFile(fileId)`: Drive fileIDを指定してインポート
- `getQuestionBankImportUrl()`: インポート用フォルダURLを取得
- `testImportQuestionBankFromCsv()`: サンプルデータでテスト

### Code.gs に追加されたエンドポイント

- `?action=importCsvFromFolder`: GETリクエストでフォルダからインポート
- `?action=getImportFolderUrl`: GETリクエストでフォルダURL取得
- `POST { action: 'importCsvText', csvText: '...' }`: CSVテキストを直接インポート

---

## セキュリティ注意事項

**重要**: Web アプリを「全員」アクセス可能にすると、誰でもQuestionBankシートを上書きできます。

推奨事項:
- インポート完了後、デプロイ設定を元に戻す（認証必須に）
- または、Google Drive経由の方法のみを使用する（認証不要）
