# Google Sheets自動アップロードスクリプト

CSVファイルをGoogle Sheetsに自動的にインポートするスクリプトです。

## 機能

- CSVファイル (`questionbank_drive_import.csv`) を読み込み
- Google Sheets APIを使ってQuestionBankシートのデータを**完全に置き換え**
- clasp認証情報を自動的に使用（既存の認証情報を活用）

## ファイル

- **スクリプト**: `tools/auto_upload_to_sheets.py`
- **対象CSV**: `tools/questionbank_drive_import.csv`
- **対象スプレッドシート**: [doboku-14w-training](https://docs.google.com/spreadsheets/d/1jj3AgZR2jAbgUIPtFRtjSfO0R0u5K_fiZyYQMwhEbM0/edit)

## 必要な準備

### 1. ライブラリのインストール

```bash
pip install gspread google-auth google-auth-oauthlib google-auth-httplib2
```

### 2. Google Sheets APIの有効化

初回実行時に以下のエラーが表示された場合:

```
Google Sheets APIの有効化が必要です
```

以下の手順でAPIを有効化してください:

1. 表示されたURLをブラウザで開く（例: `https://console.developers.google.com/apis/api/sheets.googleapis.com/overview?project=1072944905499`）
2. 「有効にする」ボタンをクリック
3. 数分待ってから、スクリプトを再実行

## 使い方

```bash
python tools/auto_upload_to_sheets.py
```

## 実行フロー

```
[1/4] CSVファイルを確認中...
  ✅ ファイル確認: questionbank_drive_import.csv
  - フルパス: C:\ProgramData\Generative AI\Github\doboku-14w-training\tools\questionbank_drive_import.csv

[2/4] CSVデータを読み込み中...
  ✅ 読み込み完了:
     - ヘッダー: 30列
     - データ: 682問

[3/4] Google Sheets APIに接続中...
  - clasp認証情報を使用: .clasprc.json
  ✅ 認証成功
  ✅ スプレッドシートを開きました: doboku-14w-training

[4/4] データをアップロード中...
  - スプレッドシートID: 1jj3AgZR2jAbgUIPtFRtjSfO0R0u5K_fiZyYQMwhEbM0
  - シート名: QuestionBank
  - アップロード件数: 683行（ヘッダー含む）
  - 既存データをクリア中...
  - 新しいデータをアップロード中...

======================================================================
✅ アップロード完了！
======================================================================

アップロード結果:
  - ヘッダー: 30列
  - データ: 682問

スプレッドシートURL:
  https://docs.google.com/spreadsheets/d/1jj3AgZR2jAbgUIPtFRtjSfO0R0u5K_fiZyYQMwhEbM0/edit
======================================================================
```

## エラー対処

### 1. 認証情報が見つかりません

clasp認証情報（`.clasprc.json`）が見つからない場合、以下のいずれかを配置してください:

- **clasp認証情報（推奨）**: `.clasprc.json`
- **サービスアカウント認証**: `~/.config/gspread/credentials.json`

### 2. Google Sheets APIが有効化されていません

スクリプトが表示するURLにアクセスして、APIを有効化してください。

### 3. 権限エラー

スプレッドシートへのアクセス権限がない場合、スプレッドシートの共有設定を確認してください。

## 認証方式

このスクリプトは以下の認証方式に対応しています:

1. **clasp認証情報（自動）**: `.clasprc.json`から認証情報を読み込み
2. **サービスアカウント認証**: `~/.config/gspread/credentials.json`
3. **OAuth2認証**: 初回実行時にブラウザで認証フロー

## 技術詳細

- **ライブラリ**: gspread + google-auth
- **認証**: clasp認証情報を再利用（OAuth2）
- **スコープ**: clasp認証のスコープをそのまま使用（`drive.file`, `script.projects`など）
- **更新方式**: 既存シートをクリアしてから一括アップロード

## 関連スクリプト

- `auto_update_sheets.py`: clasp + Apps Script方式（clasp runが使える場合）
- `auto_import_csv.py`: Playwright方式（ブラウザ自動操作）

## ライセンス

このスクリプトはdoboku-14w-trainingプロジェクトの一部です。
