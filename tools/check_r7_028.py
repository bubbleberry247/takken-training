#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""R7gakkaA-028の選択肢を確認"""

import csv

csv_path = r"C:\ProgramData\Generative AI\Github\doboku-14w-training\tools\questionbank_drive_import.csv"

with open(csv_path, 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row['qId'] == 'R7gakkaA-028':
            print("=== R7gakkaA-028 ===")
            print(f"stem: {row['stem'][:100]}...")
            print(f"\nchoiceA: '{row['choiceA']}'")
            print(f"choiceB: '{row['choiceB']}'")
            print(f"choiceC: '{row['choiceC']}'")
            print(f"choiceD: '{row['choiceD']}'")
            print(f"\ncorrectAnswer: {row['correctAnswer']}")
            break
