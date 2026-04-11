#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
71件のchoiceImageUrlを復元
画像がimagesフォルダに存在する問題のみ復元
"""

import csv
import os
from datetime import datetime
import shutil

csv_path = r"C:\ProgramData\Generative AI\Github\doboku-14w-training\tools\questionbank_drive_import.csv"
images_dir = r"C:\ProgramData\Generative AI\Github\doboku-14w-training\images"
backup_path = csv_path.replace('.csv', f'_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv')

# GitHub raw content URL template
url_template = "https://raw.githubusercontent.com/bubbleberry247/PDF-RakuRaku-Seisan/master/docs/assets/doboku-14w/images/{}.png"

print(f"CSVファイルを読み込み中: {csv_path}")

# バックアップ作成
shutil.copy(csv_path, backup_path)
print(f"バックアップ作成: {backup_path}\n")

# imagesフォルダ内の画像ファイルリストを取得
image_files = set()
for filename in os.listdir(images_dir):
    if filename.endswith('.png') and not '_choice' in filename:
        qid = filename.replace('.png', '')
        image_files.add(qid)

print(f"imagesフォルダ内の画像ファイル: {len(image_files)}件\n")

# CSVを読み込み
with open(csv_path, 'r', encoding='utf-8-sig', newline='') as f:
    reader = csv.DictReader(f)
    rows = list(reader)
    fieldnames = reader.fieldnames

print(f"総行数: {len(rows)}\n")

restored_count = 0

for row in rows:
    qid = row['qId']

    # 画像ファイルが存在し、かつchoiceA-Dがテキストで入っている場合のみ復元
    if qid in image_files:
        choice_a = row.get('choiceA', '').strip()
        choice_b = row.get('choiceB', '').strip()

        # テキスト選択肢がある場合は復元対象
        if choice_a and choice_b:
            # choiceImageUrlを設定
            row['choiceImageUrl'] = url_template.format(qid)
            restored_count += 1
            print(f"[{restored_count:2d}] {qid}: choiceImageUrl復元")

print(f"\n復元完了: {restored_count}件")

# CSVを書き込み
with open(csv_path, 'w', encoding='utf-8-sig', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print(f"\n保存完了: {csv_path}")
print(f"バックアップ: {backup_path}")
