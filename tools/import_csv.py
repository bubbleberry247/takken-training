#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CSVインポートスクリプト

使用方法:
    python import_csv.py

機能:
    1. questionbank_drive_import.csv を読み込み
    2. Apps Script の doPost エンドポイントにPOST
    3. QuestionBankシートを全削除してCSVデータをインポート
"""

import os
import sys
import io
import json
import requests

# UTF-8出力設定（Windows対応）
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 定数
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(SCRIPT_DIR, 'questionbank_drive_import.csv')
DEPLOY_URL = 'https://script.google.com/macros/s/AKfycbx9f7KnJ5WMuH3T3AWrewGaU14V5k8xn4uelGlxB9YFZyOL-So2IcF_D7J5jmggk-vYdg/exec'


def read_csv_file(csv_path):
    """CSVファイルを読み込む"""
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        csv_text = f.read()

    print(f"CSV file loaded: {csv_path}")
    print(f"CSV size: {len(csv_text):,} bytes")
    print(f"CSV lines: {csv_text.count(chr(10)) + 1}")

    return csv_text


def import_csv_via_post(csv_text):
    """POST リクエストでCSVをインポート"""
    payload = {
        'action': 'importCsvText',
        'csvText': csv_text
    }

    print("\nSending CSV data to Apps Script...")
    print(f"Payload size: {len(json.dumps(payload)):,} bytes")

    try:
        response = requests.post(
            DEPLOY_URL,
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=300  # 5分タイムアウト
        )

        response.raise_for_status()
        result = response.json()

        print("\n=== Import Result ===")
        print(json.dumps(result, indent=2, ensure_ascii=False))

        return result

    except requests.exceptions.Timeout:
        print("ERROR: Request timeout (5 minutes). Apps Script execution may have exceeded time limit.")
        return {"ok": False, "error": "Request timeout"}

    except requests.exceptions.RequestException as e:
        print(f"ERROR: Request failed: {e}")
        return {"ok": False, "error": str(e)}


def main():
    """メイン処理"""
    print("=== QuestionBank CSV Import Tool ===\n")

    # CSVファイルを読み込み
    try:
        csv_text = read_csv_file(CSV_PATH)
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    # インポート実行
    result = import_csv_via_post(csv_text)

    # 結果判定
    if result.get('ok'):
        print(f"\n[SUCCESS] Imported {result.get('rowsImported', 0)} questions")
        sys.exit(0)
    else:
        error_msg = result.get('error', 'Unknown error')
        print(f"\n[FAILED] {error_msg}")
        sys.exit(1)


if __name__ == '__main__':
    main()
