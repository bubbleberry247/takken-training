#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""choiceImageUrlが設定されているがテキスト選択肢を持つ問題を検出"""

import csv

csv_path = r"C:\ProgramData\Generative AI\Github\doboku-14w-training\tools\questionbank_drive_import.csv"

with open(csv_path, 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    rows = list(reader)

print(f"=== choiceImageUrlが設定されている問題を調査 ===\n")

problems = []
for row in rows:
    choice_image_url = row.get('choiceImageUrl', '').strip()
    if choice_image_url and choice_image_url != '...':
        # choiceImageUrlがあり、かつテキスト選択肢もある場合
        choice_a = row.get('choiceA', '').strip()
        choice_b = row.get('choiceB', '').strip()

        if choice_a or choice_b:  # テキスト選択肢がある
            problems.append({
                'qId': row['qId'],
                'choiceA_len': len(choice_a),
                'choiceB_len': len(choice_b),
                'choiceC_len': len(row.get('choiceC', '').strip()),
                'choiceD_len': len(row.get('choiceD', '').strip()),
                'choiceA_preview': choice_a[:50] if choice_a else ''
            })

print(f"choiceImageUrlが設定されているがテキスト選択肢もある問題: {len(problems)}件\n")

for p in problems:
    print(f"{p['qId']}")
    print(f"  choiceA ({p['choiceA_len']}字): {p['choiceA_preview']}...")
    print(f"  choiceB ({p['choiceB_len']}字), choiceC ({p['choiceC_len']}字), choiceD ({p['choiceD_len']}字)")
    print()

print(f"\n=== 修正対象のqIdリスト ===")
print([p['qId'] for p in problems])
