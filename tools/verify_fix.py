#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""修正内容を確認"""

import csv

csv_path = r"C:\ProgramData\Generative AI\Github\doboku-14w-training\tools\questionbank_drive_import.csv"

with open(csv_path, 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row['qId'] == 'R3gakkaB-031':
            print("=== R3gakkaB-031 (修正後) ===")
            print(row['stem'])
            print("\n" + "="*60)
            break
