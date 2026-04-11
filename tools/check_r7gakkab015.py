#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""R7gakkaB-015のchoiceImageUrlを確認"""

import csv

csv_path = r"C:\ProgramData\Generative AI\Github\doboku-14w-training\tools\questionbank_drive_import.csv"

with open(csv_path, 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row['qId'] == 'R7gakkaB-015':
            print("=== R7gakkaB-015 ===")
            print(f"stem (first 100 chars): {row['stem'][:100]}...")
            print(f"\nimageUrl: {row.get('imageUrl', 'N/A')}")
            print(f"choiceImageUrl: {row.get('choiceImageUrl', 'N/A')}")
            print(f"\nchoiceA (first 100 chars): {row.get('choiceA', '')[:100]}")
            print(f"choiceB (first 100 chars): {row.get('choiceB', '')[:100]}")
            print(f"choiceC (first 100 chars): {row.get('choiceC', '')[:100]}")
            print(f"choiceD (first 100 chars): {row.get('choiceD', '')[:100]}")
            break
