#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""R7gakkaA-025の選択肢1を確認"""

import csv

csv_path = r"C:\ProgramData\Generative AI\Github\doboku-14w-training\tools\questionbank_drive_import.csv"

with open(csv_path, 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row['qId'] == 'R7gakkaA-025':
            print("=== R7gakkaA-025 ===")
            print(f"choiceA: {row['choiceA']}")
            print(f"\n先頭文字: '{row['choiceA'][:10]}'")
            break
