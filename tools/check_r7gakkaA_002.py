#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import io
import csv

# UTF-8出力設定
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

with open(r'C:\ProgramData\Generative AI\Github\doboku-14w-training\tools\questionbank_drive_import.csv', 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row.get('qId') == 'R7gakkaA-002':
            print('qId:', row.get('qId', ''))
            print('choiceA:', row.get('choiceA', ''))
            print()
            print('choiceB:', row.get('choiceB', ''))
            print()
            print('choiceC:', row.get('choiceC', ''))
            print()
            print('choiceD:', row.get('choiceD', ''))
            print()
            print('correct:', row.get('correct', ''))
            break
