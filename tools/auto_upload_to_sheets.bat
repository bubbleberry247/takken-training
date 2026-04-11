@echo off
REM Google Sheets自動アップロードスクリプト実行用バッチファイル
REM ダブルクリックで実行可能

cd /d "%~dp0"

echo ======================================================================
echo Google Sheets 自動アップロード
echo ======================================================================
echo.

python auto_upload_to_sheets.py

echo.
pause
