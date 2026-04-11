#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
選択肢から不要な注意書きを削除するスクリプト
"""
import csv
import sys
import re
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

CSV_PATH = Path(r"C:\ProgramData\Generative AI\Github\doboku-14w-training\tools\questionbank_drive_import.csv")

# CSVを読み込み
with open(CSV_PATH, 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    rows = list(reader)
    fieldnames = reader.fieldnames

updated_count = 0

# 各行の選択肢から不要な文章を削除
for row in rows:
    for field in ['choiceA', 'choiceB', 'choiceC', 'choiceD']:
        original = row.get(field, '')
        if '※ 問題番号' in original:
            # 「※ 問題番号」以降を削除
            cleaned = re.sub(r'\s*※\s*問題番号.*$', '', original, flags=re.DOTALL)
            cleaned = cleaned.strip()

            if cleaned != original:
                row[field] = cleaned
                print(f'✓ {row["qId"]} {field}: 不要な文章を削除')
                updated_count += 1

# CSVに書き戻し
with open(CSV_PATH, 'w', encoding='utf-8-sig', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print(f'\n=== 処理完了 ===')
print(f'更新件数: {updated_count}件')
print(f'合計問題数: {len(rows)}件')
