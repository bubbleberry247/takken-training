#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CSV を Apps Script エディタに貼り付け可能な形式に変換

使用方法:
    python prepare_csv_for_paste.py > csv_for_paste.txt

出力されたテキストを Apps Script エディタで使用:
    1. Apps Script エディタを開く
    2. importCsv.gs を開く
    3. 以下の関数を新規作成:

    function runImportFromPastedCsv() {
      var csvText = `<ここに csv_for_paste.txt の内容を貼り付け>`;
      Logger.log('Importing CSV...');
      var result = importQuestionBankFromCsv(csvText);
      Logger.log('Result: ' + JSON.stringify(result));
      return result;
    }

    4. runImportFromPastedCsv を実行
"""

import os
import sys
import io

# UTF-8出力設定
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(SCRIPT_DIR, 'questionbank_drive_import.csv')


def main():
    if not os.path.exists(CSV_PATH):
        print(f"ERROR: CSV file not found: {CSV_PATH}", file=sys.stderr)
        sys.exit(1)

    with open(CSV_PATH, 'r', encoding='utf-8-sig') as f:
        csv_text = f.read()

    # JavaScriptテンプレートリテラル用にエスケープ
    csv_escaped = csv_text.replace('\\', '\\\\')  # バックスラッシュ
    csv_escaped = csv_escaped.replace('`', '\\`')  # バッククォート
    csv_escaped = csv_escaped.replace('${', '\\${')  # テンプレート変数

    # 出力
    print(csv_escaped)

    # 統計情報（stderr に出力してファイルに混入しないようにする）
    print(f"\n[INFO] CSV size: {len(csv_text):,} bytes", file=sys.stderr)
    print(f"[INFO] CSV lines: {csv_text.count(chr(10)) + 1}", file=sys.stderr)
    print(f"[INFO] Escaped size: {len(csv_escaped):,} bytes", file=sys.stderr)


if __name__ == '__main__':
    main()
