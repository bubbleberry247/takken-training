#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Google Sheets自動更新スクリプト（clasp認証利用版）

使用方法:
  python auto_update_sheets.py
"""
import sys
import io
import csv
import json
import subprocess
from pathlib import Path

# UTF-8出力設定
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 設定
CSV_FILE = Path(__file__).parent / 'questionbank_drive_import.csv'
SPREADSHEET_ID = '1jj3AgZR2jAbgUIPtFRtjSfO0R0u5K_fiZyYQMwhEbM0'
SHEET_NAME = 'QuestionBank'
PROJECT_DIR = Path(__file__).parent.parent

print("=" * 70)
print("Google Sheets 自動更新（clasp認証利用）")
print("=" * 70)

# ステップ1: CSVデータを読み込み
print(f"\n[1/3] CSVファイルを読み込み中: {CSV_FILE.name}")
rows = []
with open(CSV_FILE, 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    fieldnames = list(reader.fieldnames)
    for row in reader:
        rows.append(row)

print(f"  ✅ 読み込み完了: {len(rows)}問、{len(fieldnames)}列")

# ステップ2: Google Apps Scriptを使用してシート更新
print(f"\n[2/3] Google Sheetsを更新中...")
print(f"  - スプレッドシートID: {SPREADSHEET_ID}")
print(f"  - シート名: {SHEET_NAME}")

# 一時的なJSファイルを作成
update_script = f"""
function updateQuestionBankFromLocal() {{
  var ss = SpreadsheetApp.openById('{SPREADSHEET_ID}');
  var sheet = ss.getSheetByName('{SHEET_NAME}');

  if (!sheet) {{
    throw new Error('シート "{SHEET_NAME}" が見つかりません');
  }}

  // シートをクリア
  sheet.clear();

  // ヘッダー行を設定
  var headers = {json.dumps(fieldnames)};
  sheet.appendRow(headers);

  // データを50行ずつバッチで追加（API制限回避）
  var data = {json.dumps([[row.get(f, '') for f in fieldnames] for row in rows])};

  Logger.log('総行数: ' + data.length);

  for (var i = 0; i < data.length; i += 50) {{
    var batch = data.slice(i, i + 50);
    if (batch.length > 0) {{
      sheet.getRange(i + 2, 1, batch.length, headers.length).setValues(batch);
      Logger.log('進行状況: ' + (i + batch.length) + ' / ' + data.length);
    }}
  }}

  return {{ success: true, rows: data.length }};
}}
"""

temp_file = PROJECT_DIR / 'src' / 'tempUpdate.gs'
with open(temp_file, 'w', encoding='utf-8') as f:
    f.write(update_script)

print(f"  - 一時スクリプト作成: {temp_file.name}")

# clasp pushで一時ファイルをアップロード
print(f"  - Apps Scriptにアップロード中...")
result = subprocess.run(
    ['npx', 'clasp', 'push'],
    capture_output=True,
    text=True,
    cwd=PROJECT_DIR
)

if result.returncode != 0:
    print(f"  ❌ アップロードエラー: {result.stderr}")
    temp_file.unlink()
    sys.exit(1)

print(f"  ✅ アップロード完了")

# Apps Scriptエディタで関数を実行
print(f"\n[3/3] 更新関数を実行中...")
print(f"  ⚠️  この処理には時間がかかる場合があります...")

# clasp runで関数を実行
result = subprocess.run(
    ['npx', 'clasp', 'run', 'updateQuestionBankFromLocal'],
    capture_output=True,
    text=True,
    cwd=PROJECT_DIR
)

# 一時ファイルを削除
temp_file.unlink()
print(f"  - 一時ファイル削除: {temp_file.name}")

if result.returncode != 0:
    print(f"\n❌ 実行エラー:")
    print(result.stderr)
    print("\n" + "=" * 70)
    print("⚠️  clasp runが利用できない場合の代替手順:")
    print("=" * 70)
    print("1. Apps Scriptエディタを開く:")
    print("   https://script.google.com/home/projects/1giv21Jbc8lSmC8fQ3TDJ6gNP7-nH2m2KnPAYebhd0rK8B65gc0mvFzKS")
    print("\n2. コンソールで以下を実行:")
    print("   updateQuestionBankFromLocal()")
    print("=" * 70)
    sys.exit(1)

print(f"\n" + "=" * 70)
print(f"✅ Google Sheets更新完了！")
print(f"=" * 70)
print(f"\n次のステップ:")
print(f"  1. Webアプリを開く")
print(f"  2. Ctrl+F5で強制再読み込み")
print(f"  3. 画像エラー・選択肢重複が解消されていることを確認")
print(f"=" * 70)
