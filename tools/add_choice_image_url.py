#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CSVに choiceImageUrl カラムを追加し、選択肢画像が存在する問題にURLを設定
"""
import sys
import io
import csv

# UTF-8出力設定
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 選択肢画像のマッピング（単一画像形式のみ）
# R5gakkaA-020.png は選択肢画像として使用（問題図はない → imageUrlを空にする）
# R6gakkaA-005_choice.png は問題図とは別に存在
choice_image_mapping = {
    'R5gakkaA-020': {
        'choiceImageUrl': 'https://raw.githubusercontent.com/bubbleberry247/PDF-RakuRaku-Seisan/master/docs/assets/doboku-14w/images/R5gakkaA-020.png',
        'clearImageUrl': True  # imageUrlを空にする
    },
    'R6gakkaA-005': {
        'choiceImageUrl': 'https://raw.githubusercontent.com/bubbleberry247/PDF-RakuRaku-Seisan/master/docs/assets/doboku-14w/images/R6gakkaA-005_choice.png',
        'clearImageUrl': False  # imageUrlは維持（問題図がある）
    },
}

# questionbank_drive_import.csvを読み込み
input_file = r'C:\ProgramData\Generative AI\Github\doboku-14w-training\tools\questionbank_drive_import.csv'
output_file = r'C:\ProgramData\Generative AI\Github\doboku-14w-training\tools\questionbank_drive_import.csv'

rows = []
updated_count = 0

with open(input_file, 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    fieldnames = reader.fieldnames

    # choiceImageUrl フィールドを imageUrl の後に追加
    if 'choiceImageUrl' not in fieldnames:
        # imageUrl の位置を探す
        imageUrl_index = fieldnames.index('imageUrl')
        new_fieldnames = list(fieldnames[:imageUrl_index + 1]) + ['choiceImageUrl'] + list(fieldnames[imageUrl_index + 1:])
    else:
        new_fieldnames = fieldnames

    for row in reader:
        qid = row.get('qId', '').strip()

        # choiceImageUrl フィールドを追加
        if 'choiceImageUrl' not in row:
            row['choiceImageUrl'] = ''

        # 選択肢画像が存在する問題にURLを設定
        if qid in choice_image_mapping:
            config = choice_image_mapping[qid]
            row['choiceImageUrl'] = config['choiceImageUrl']
            if config.get('clearImageUrl', False):
                row['imageUrl'] = ''
                print(f"{qid}: 選択肢画像URL設定 (imageUrlクリア)")
            else:
                print(f"{qid}: 選択肢画像URL設定")
            updated_count += 1

        rows.append(row)

# 修正したデータを書き込み
with open(output_file, 'w', encoding='utf-8-sig', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=new_fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print(f"\n処理完了:")
print(f"  - choiceImageUrlフィールド追加")
print(f"  - 選択肢画像URL設定: {updated_count}問")
print(f"  - 合計: {len(rows)}問")
