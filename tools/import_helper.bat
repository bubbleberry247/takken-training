@echo off
chcp 65001 >nul
echo ================================================================
echo Google Sheets CSV インポート補助ツール
echo ================================================================
echo.
echo このツールは以下を自動で開きます:
echo   1. CSVファイルの場所（エクスプローラー）
echo   2. Google Sheets（ブラウザ）
echo   3. インポート手順（メモ帳）
echo.
pause

REM CSVファイルの場所を開く
echo [1/3] CSVファイルの場所を開いています...
explorer /select,"%~dp0questionbank_drive_import.csv"
timeout /t 2 /nobreak >nul

REM Google Sheetsを開く
echo [2/3] Google Sheetsをブラウザで開いています...
start https://docs.google.com/spreadsheets/d/1jj3AgZR2jAbgUIPtFRtjSfO0R0u5K_fiZyYQMwhEbM0/edit
timeout /t 2 /nobreak >nul

REM 手順をメモ帳で表示
echo [3/3] インポート手順を表示しています...
(
echo ================================================================
echo Google Sheets CSVインポート手順
echo ================================================================
echo.
echo 【手順1】QuestionBankシートを選択
echo   - 画面下部のシートタブから「QuestionBank」をクリック
echo.
echo 【手順2】ファイル → インポート
echo   - 左上の「ファイル」メニューをクリック
echo   - 「インポート」を選択
echo.
echo 【手順3】アップロード
echo   - 「アップロード」タブを選択
echo   - エクスプローラーから「questionbank_drive_import.csv」を
echo     ドラッグ＆ドロップ
echo.
echo 【手順4】インポート設定
echo   - インポート場所: 「現在のシートを置き換える」を選択
echo   - 区切り文字: 自動検出（カンマ）
echo.
echo 【手順5】データをインポート
echo   - 「データをインポート」ボタンをクリック
echo   - 完了を待つ（数秒〜数十秒）
echo.
echo 【手順6】Webアプリで確認
echo   - Webアプリを開く
echo   - Ctrl+F5で強制再読み込み
echo   - 画像エラー・選択肢重複が解消されていることを確認
echo.
echo ================================================================
) > "%TEMP%\google_sheets_import_steps.txt"
notepad "%TEMP%\google_sheets_import_steps.txt"

echo.
echo ================================================================
echo 準備完了！上記の手順に従ってインポートしてください。
echo ================================================================
pause
