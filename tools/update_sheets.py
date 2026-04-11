#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Google Sheetsに最新のQuestionBankデータを自動アップロードするスクリプト

使用方法:
  python update_sheets.py
"""
import sys
import io
import csv
import json
import requests
from pathlib import Path

# UTF-8出力設定
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 設定
CSV_FILE = Path(__file__).parent / 'questionbank_drive_import.csv'
GAS_DEPLOY_URL = 'https://script.google.com/macros/s/AKfycbx9f7KnJ5WMuH3T3AWrewGaU14V5k8xn4uelGlxB9YFZyOL-So2IcF_D7J5jmggk-vYdg/exec'

def read_csv_data():
    """CSVファイルを読み込み"""
    print(f"CSVファイルを読み込み中: {CSV_FILE}")

    rows = []
    with open(CSV_FILE, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames

        for row in reader:
            rows.append(row)

    print(f"  - 読み込み完了: {len(rows)}問")
    return fieldnames, rows

def upload_to_sheets(fieldnames, rows):
    """Google Sheetsにデータをアップロード"""
    print("\nGoogle Sheetsにアップロード中...")

    # データをJSON形式に変換
    payload = {
        'action': 'updateQuestionBank',
        'fieldnames': list(fieldnames),
        'rows': rows
    }

    # GASエンドポイントにPOST
    try:
        response = requests.post(
            GAS_DEPLOY_URL,
            json=payload,
            timeout=300  # 5分タイムアウト
        )

        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print(f"✅ アップロード成功: {result.get('message')}")
                return True
            else:
                print(f"❌ エラー: {result.get('error')}")
                return False
        else:
            print(f"❌ HTTPエラー: {response.status_code}")
            print(response.text)
            return False

    except Exception as e:
        print(f"❌ 例外エラー: {e}")
        return False

def main():
    print("=" * 60)
    print("Google Sheets QuestionBank 自動更新")
    print("=" * 60)

    # CSVデータを読み込み
    fieldnames, rows = read_csv_data()

    # Google Sheetsにアップロード
    success = upload_to_sheets(fieldnames, rows)

    print("\n" + "=" * 60)
    if success:
        print("✅ 更新完了")
        print("\n次のステップ:")
        print("  1. Webアプリを開く")
        print("  2. Ctrl+F5で強制再読み込み")
        print("  3. 画像エラー・選択肢重複が解消されていることを確認")
    else:
        print("❌ 更新失敗")
        print("\n手動インポート手順:")
        print("  1. https://docs.google.com/spreadsheets/d/1jj3AgZR2jAbgUIPtFRtjSfO0R0u5K_fiZyYQMwhEbM0/edit")
        print("  2. ファイル → インポート → アップロード")
        print(f"  3. {CSV_FILE}")
        print("  4. インポート場所: 現在のシートを置き換える")
    print("=" * 60)

if __name__ == '__main__':
    main()
