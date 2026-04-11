#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import csv
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

with open('questionbank_drive_import.csv', 'r', encoding='utf-8-sig', newline='') as f:
    reader = csv.DictReader(f)
    for i, row in enumerate(reader, 1):
        if '径,かぶり' in row.get('choiceD', ''):
            print(f"行{i}: qId={row['qId']}, choiceD に「径,かぶり」を発見")
            print(f"  choiceD内容: {row['choiceD'][:100]}")
