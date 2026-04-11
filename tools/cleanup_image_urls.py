#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
画像が存在しない問題のimageUrlフィールドを空にするスクリプト
"""
import sys
import io
import csv

# UTF-8出力設定
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# image_mapping.csvから実際に存在する画像のqIdリストを取得
existing_image_qids = set()
with open(r'C:\ProgramData\Generative AI\Github\doboku-14w-training\images\image_mapping.csv', 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    for row in reader:
        qid = row.get('qId', '').strip()
        if qid:
            existing_image_qids.add(qid)

print(f"実際に画像が存在するqId数: {len(existing_image_qids)}")

# questionbank_drive_import.csvを読み込み、修正
input_file = r'C:\ProgramData\Generative AI\Github\doboku-14w-training\tools\questionbank_drive_import.csv'
output_file = r'C:\ProgramData\Generative AI\Github\doboku-14w-training\tools\questionbank_drive_import.csv'

rows = []
cleared_count = 0
kept_count = 0

with open(input_file, 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    fieldnames = reader.fieldnames

    for row in reader:
        qid = row.get('qId', '').strip()

        # qIdが存在する画像リストに含まれていない場合、imageUrlを空にする
        if qid not in existing_image_qids:
            if row.get('imageUrl', '').strip():  # 既にURLがある場合のみカウント
                cleared_count += 1
            row['imageUrl'] = ''
        else:
            kept_count += 1

        rows.append(row)

# 修正したデータを書き込み
with open(output_file, 'w', encoding='utf-8-sig', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print(f"\n処理完了:")
print(f"  - imageUrlを保持: {kept_count}問")
print(f"  - imageUrlを削除: {cleared_count}問")
print(f"  - 合計: {kept_count + cleared_count}問")
