#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""箇条書き（・）を改行して文頭に配置"""

import csv
import re

csv_path = r"C:\ProgramData\Generative AI\Github\doboku-14w-training\tools\questionbank_drive_import.csv"

print("=== 箇条書き改行修正 ===\n")

with open(csv_path, 'r', encoding='utf-8-sig', newline='') as f:
    reader = csv.DictReader(f)
    fieldnames = reader.fieldnames
    rows = list(reader)

# 1. imageUrl == choiceImageUrlの場合、choiceImageUrlを削除
duplicate_image_count = 0
for row in rows:
    if row['imageUrl'] and row['choiceImageUrl']:
        if row['imageUrl'] == row['choiceImageUrl']:
            row['choiceImageUrl'] = ''
            duplicate_image_count += 1

print(f"[INFO] 重複画像URL削除: {duplicate_image_count}件\n")

# 2. 箇条書き（・）を改行
bullet_pattern = re.compile(r'([。\n])\s*・')
modified_count = 0
modified_qids = []

for row in rows:
    original_stem = row['stem']

    # 「・」の前に改行を挿入（。または改行の後にある・を改行+・に変換）
    modified_stem = bullet_pattern.sub(r'\1\n・', original_stem)

    if modified_stem != original_stem:
        row['stem'] = modified_stem
        modified_count += 1
        if len(modified_qids) < 10:
            modified_qids.append(row['qId'])

print(f"[INFO] 箇条書き改行修正: {modified_count}件")
if modified_qids:
    print(f"例: {', '.join(modified_qids)}")
    if modified_count > 10:
        print(f"... 他 {modified_count - 10}件")

# CSVを書き出し
with open(csv_path, 'w', encoding='utf-8-sig', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print(f"\n[OK] {csv_path} を更新しました")
print("\n次の手順:")
print("1. Google Sheetsでファイル → インポート")
print("2. questionbank_drive_import.csv をアップロード")
print("3. 'シートを置き換える'を選択")
