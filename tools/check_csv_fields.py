#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""CSVのフィールド数を詳細チェック"""

import csv

csv_path = r"C:\ProgramData\Generative AI\Github\doboku-14w-training\tools\questionbank_drive_import.csv"

with open(csv_path, 'r', encoding='utf-8-sig', newline='') as f:
    reader = csv.DictReader(f)
    fieldnames = reader.fieldnames
    expected_count = len(fieldnames)

    print(f"期待するフィールド数: {expected_count}")
    print(f"フィールド名: {', '.join(fieldnames[:5])}...\n")

    error_count = 0
    for i, row in enumerate(reader, start=2):
        actual_count = len(row.values())
        # dictreaderはフィールド数が多い場合、余分なフィールドをNoneキーに格納する
        if None in row:
            print(f"行{i} ({row.get('qId', 'unknown')}): フィールド数過多")
            print(f"  余分なデータ: {row[None]}")
            error_count += 1
            if error_count >= 5:
                break

    if error_count == 0:
        print("[OK] csvモジュールで読み取った結果、フィールド数の問題なし")
    else:
        print(f"\n[ERROR] {error_count}件以上のフィールド数エラーを検出")
