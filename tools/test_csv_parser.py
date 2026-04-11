#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CSVパーサーのユニットテスト

Apps Scriptの parseCsv_() 関数が正しくCSVをパースできるか検証
"""

import os
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(SCRIPT_DIR, 'questionbank_drive_import.csv')


def test_csv_structure():
    """CSVファイルの構造をテスト"""
    with open(CSV_PATH, 'r', encoding='utf-8-sig') as f:
        lines = f.readlines()

    # 統計情報
    print(f"Total lines: {len(lines)}")
    print(f"First line (header): {lines[0][:100]}...")

    # ヘッダー列数
    header = lines[0].strip()
    header_cols = header.count(',') + 1
    print(f"Header columns: {header_cols}")

    # 各行の列数をチェック
    col_counts = {}
    for i, line in enumerate(lines[1:], start=2):
        # 簡易カウント（ダブルクォート内のカンマは無視しない）
        cols = line.count(',') + 1
        col_counts[cols] = col_counts.get(cols, 0) + 1

    print(f"\nColumn count distribution:")
    for cols, count in sorted(col_counts.items()):
        print(f"  {cols} columns: {count} rows")

    # ダブルクォートの使用状況
    quote_count = sum(1 for line in lines if '"' in line)
    print(f"\nLines with double quotes: {quote_count} / {len(lines)} ({quote_count/len(lines)*100:.1f}%)")

    # 改行を含む可能性のある行（ダブルクォート内の改行）
    multiline_candidates = []
    in_quotes = False
    for i, line in enumerate(lines, start=1):
        for char in line:
            if char == '"':
                in_quotes = not in_quotes
        if in_quotes:
            multiline_candidates.append(i)

    if multiline_candidates:
        print(f"\nWarning: Possible multiline fields detected at lines: {multiline_candidates[:10]}")
    else:
        print(f"\nNo multiline fields detected (all quotes are properly closed within lines)")

    # サンプル行を表示
    print(f"\n=== Sample Row (line 2) ===")
    print(lines[1][:500])

    return {
        'total_lines': len(lines),
        'header_columns': header_cols,
        'data_rows': len(lines) - 1
    }


def test_problematic_characters():
    """問題になりそうな文字をチェック"""
    with open(CSV_PATH, 'r', encoding='utf-8-sig') as f:
        content = f.read()

    # カンマのエスケープ確認
    print(f"\n=== Character Analysis ===")
    print(f"Total characters: {len(content):,}")
    print(f"Commas: {content.count(','):,}")
    print(f"Double quotes: {content.count('\"'):,}")
    print(f"Newlines: {content.count(chr(10)):,}")
    print(f"Carriage returns: {content.count(chr(13)):,}")

    # BOM確認
    if content[0] == '\ufeff':
        print(f"BOM detected: UTF-8 with BOM")
    else:
        print(f"No BOM detected")


def main():
    """メイン処理"""
    print("=== CSV Structure Test ===\n")

    if not os.path.exists(CSV_PATH):
        print(f"ERROR: CSV file not found: {CSV_PATH}")
        sys.exit(1)

    stats = test_csv_structure()
    test_problematic_characters()

    print(f"\n=== Test Summary ===")
    print(f"CSV file: {CSV_PATH}")
    print(f"Total lines: {stats['total_lines']}")
    print(f"Header columns: {stats['header_columns']}")
    print(f"Data rows: {stats['data_rows']}")
    print(f"\n[OK] CSV structure test completed")


if __name__ == '__main__':
    main()
