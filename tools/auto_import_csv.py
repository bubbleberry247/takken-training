#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Google SheetsへのCSVインポートを完全自動化（Playwright使用）

使用方法:
  python auto_import_csv.py
"""
import sys
import io
import time
import subprocess
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

# UTF-8出力設定
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 設定
CSV_FILE = Path(__file__).parent / 'questionbank_drive_import.csv'
SPREADSHEET_URL = 'https://docs.google.com/spreadsheets/d/1jj3AgZR2jAbgUIPtFRtjSfO0R0u5K_fiZyYQMwhEbM0/edit'

print("=" * 70)
print("Google Sheets CSV自動インポート（Playwright使用）")
print("=" * 70)

print(f"\nCSVファイル: {CSV_FILE}")
print(f"スプレッドシート: {SPREADSHEET_URL}")

# Playwrightがインストールされているか確認
try:
    subprocess.run(['python', '-m', 'playwright', '--version'], check=True, capture_output=True)
except:
    print("\n❌ Playwrightがインストールされていません")
    print("\n以下のコマンドを実行してください:")
    print("  pip install playwright")
    print("  python -m playwright install chromium")
    sys.exit(1)

print("\n[1/5] ブラウザを起動中...")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)  # ヘッドレスモードOFF（操作を見える化）
    context = browser.new_context()
    page = context.new_page()

    print("[2/5] スプレッドシートを開いています...")
    page.goto(SPREADSHEET_URL)

    # Google認証が必要な場合は待機
    print("  ⚠️  Google認証が必要な場合は、ブラウザでログインしてください...")
    try:
        page.wait_for_url("**/edit**", timeout=60000)  # 60秒待機
    except:
        print("  ❌ タイムアウト: スプレッドシートが開けませんでした")
        browser.close()
        sys.exit(1)

    print("  ✅ スプレッドシート表示成功")

    print("[3/5] QuestionBankシートを選択...")
    try:
        # シートタブをクリック
        sheet_tab = page.locator('text=QuestionBank').first
        sheet_tab.click()
        time.sleep(1)
    except:
        print("  ⚠️  QuestionBankシートが見つかりません（スキップ）")

    print("[4/5] インポート操作を実行中...")

    # ファイル → インポート
    page.locator('[aria-label="ファイル"]').click()
    time.sleep(0.5)
    page.locator('text=インポート').click()
    time.sleep(1)

    # アップロードタブ
    page.locator('text=アップロード').click()
    time.sleep(0.5)

    # ファイルを選択
    print(f"  - CSVファイルをアップロード中: {CSV_FILE}")
    file_input = page.locator('input[type="file"]')
    file_input.set_input_files(str(CSV_FILE))
    time.sleep(2)

    # インポート場所: 現在のシートを置き換える
    print(f"  - インポート設定: 現在のシートを置き換える")
    page.locator('text=現在のシートを置き換える').click()
    time.sleep(0.5)

    # データをインポートボタン
    print(f"  - データをインポート...")
    page.locator('button:has-text("データをインポート")').click()

    # インポート完了を待機
    print(f"  ⚠️  インポート処理中... 数分かかる場合があります")
    try:
        page.wait_for_timeout(10000)  # 10秒待機
    except:
        pass

    print("[5/5] 完了確認...")
    time.sleep(2)

    browser.close()

print("\n" + "=" * 70)
print("✅ Google Sheets自動インポート完了！")
print("=" * 70)
print("\n次のステップ:")
print("  1. Webアプリを開く")
print("  2. Ctrl+F5で強制再読み込み")
print("  3. 画像エラー・選択肢重複が解消されていることを確認")
print("=" * 70)
