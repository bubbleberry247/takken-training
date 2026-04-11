#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CSVファイルをGoogle Driveにアップロードするスクリプト

使用方法:
  python upload_csv_to_drive.py
"""
import sys
import io
import subprocess
from pathlib import Path

# UTF-8出力設定
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

CSV_FILE = Path(__file__).parent / 'questionbank_drive_import.csv'
DRIVE_FOLDER_NAME = 'doboku-14w-data'

print("=" * 60)
print("CSVファイルをGoogle Driveにアップロード")
print("=" * 60)

print(f"\nCSVファイル: {CSV_FILE}")
print(f"アップロード先: Google Drive/{DRIVE_FOLDER_NAME}/")

# clasp loginで認証確認
print("\n認証確認中...")
result = subprocess.run(
    ['npx', 'clasp', 'login', '--status'],
    capture_output=True,
    text=True,
    cwd=CSV_FILE.parent.parent
)

if result.returncode != 0:
    print("❌ clasp認証が必要です")
    print("\n以下のコマンドを実行してください:")
    print("  cd \"C:\\ProgramData\\Generative AI\\Github\\doboku-14w-training\"")
    print("  npx clasp login")
    sys.exit(1)

print("✅ 認証OK")

print("\n" + "=" * 60)
print("次のステップ:")
print("  1. Google Driveを開く")
print("  2. 新しいフォルダを作成: 'doboku-14w-data'")
print("  3. questionbank_drive_import.csv をアップロード")
print("  4. アップロード後、フォルダIDをコピー")
print("     (URL: https://drive.google.com/drive/folders/[FOLDER_ID])")
print("=" * 60)
