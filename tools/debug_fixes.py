#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修正デバッグスクリプト
"""

import sys
import io
import csv

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

CSV_FILE = r"C:\ProgramData\Generative AI\Github\doboku-14w-training\tools\questionbank_drive_import.csv"

def load_csv(filepath):
    rows = []
    with open(filepath, 'r', encoding='utf-8', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows

rows = load_csv(CSV_FILE)

# 問題の行をチェック
print("=" * 80)
print("デバッグ: 該当行の確認")
print("=" * 80)

# 行29 (CSVの行番号2から始まるので、インデックスは27)
idx = 27
print(f"\n[インデックス{idx}] 行番号{idx+2}")
print(f"qId: {rows[idx]['qId']}")
print(f"choiceA: {rows[idx]['choiceA'][:100]}")
print(f"'層の仕上り厚の/以' in choiceA: {'層の仕上り厚の/以' in rows[idx]['choiceA']}")

# 行30
idx = 28
print(f"\n[インデックス{idx}] 行番号{idx+2}")
print(f"qId: {rows[idx]['qId']}")
print(f"choiceB: {rows[idx]['choiceB'][:100]}")
print(f"'縦継目側の 〜10' in choiceB: {'縦継目側の 〜10' in rows[idx]['choiceB']}")

# 行28
idx = 26
print(f"\n[インデックス{idx}] 行番号{idx+2}")
print(f"qId: {rows[idx]['qId']}")
print(f"choiceD: {rows[idx]['choiceD'][:100]}")
print(f"'CBR が未満' in choiceD: {'CBR が未満' in rows[idx]['choiceD']}")

# 行104
idx = 102
print(f"\n[インデックス{idx}] 行番号{idx+2}")
print(f"qId: {rows[idx]['qId']}")
print(f"choiceD: {rows[idx]['choiceD'][:100]}")
print(f"'m 当たり 〜10' in choiceD: {'m 当たり 〜10' in rows[idx]['choiceD']}")

# 行121
idx = 119
print(f"\n[インデックス{idx}] 行番号{idx+2}")
print(f"qId: {rows[idx]['qId']}")
print(f"choiceD: {rows[idx]['choiceD'][:100]}")
print(f"'その/以上が地下' in choiceD: {'その/以上が地下' in rows[idx]['choiceD']}")

# 行347
idx = 345
print(f"\n[インデックス{idx}] 行番号{idx+2}")
print(f"qId: {rows[idx]['qId']}")
print(f"choiceD: {rows[idx]['choiceD'][:100]}")
print(f"'20分の/以上' in choiceD: {'20分の/以上' in rows[idx]['choiceD']}")
