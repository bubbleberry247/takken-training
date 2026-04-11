#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""選択肢が表示されない問題を調査"""

import csv
import json

csv_path = r"C:\ProgramData\Generative AI\Github\doboku-14w-training\tools\questionbank_drive_import.csv"
output_path = r"C:\ProgramData\Generative AI\Github\doboku-14w-training\tools\choice_issue_report.txt"

# 調査対象のqId候補
# Q28「午前 第2問」→ R7gakkaA-002 or R7gakkaA-028?
# Q8「午後 第3問」→ R7gakkaB-003 or R7gakkaB-008?
target_qids = [
    'R7gakkaA-002', 'R7gakkaA-028', 'R7gakkaA-008',
    'R7gakkaB-002', 'R7gakkaB-003', 'R7gakkaB-008', 'R7gakkaB-028'
]

with open(csv_path, 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    rows = [row for row in reader if row['qId'] in target_qids]

with open(output_path, 'w', encoding='utf-8') as f:
    for row in rows:
        f.write(f"\n{'='*80}\n")
        f.write(f"qId: {row['qId']}\n")
        f.write(f"questionType: {row.get('questionType', 'N/A')}\n")
        f.write(f"imageUrl: {row.get('imageUrl', 'N/A')[:100]}...\n")
        f.write(f"choiceImageUrl: {row.get('choiceImageUrl', 'N/A')[:100]}...\n")
        f.write(f"\nstem (first 200 chars): {row['stem'][:200]}...\n")
        f.write(f"\nchoiceA length: {len(row.get('choiceA', ''))}\n")
        f.write(f"choiceB length: {len(row.get('choiceB', ''))}\n")
        f.write(f"choiceC length: {len(row.get('choiceC', ''))}\n")
        f.write(f"choiceD length: {len(row.get('choiceD', ''))}\n")

        if row.get('choiceA'):
            f.write(f"\nchoiceA (first 100 chars): {row['choiceA'][:100]}...\n")
        else:
            f.write(f"\n⚠️ choiceA is EMPTY!\n")

print(f"レポートを出力しました: {output_path}")
