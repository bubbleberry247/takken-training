#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
データベースの実際の問題番号範囲を確認するスクリプト
"""
import csv
from collections import defaultdict

def main():
    data = defaultdict(list)

    with open('questionbank_drive_import.csv', 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            qid = row.get('qId', '')
            if 'gakka' in qid:
                # R1gakkaA-001 -> year='R1', part='gakkaA', num=1
                parts = qid.split('gakka')
                if len(parts) == 2:
                    year = parts[0]
                    rest = parts[1]  # A-001 or B-001
                    part = 'gakka' + rest[0]  # gakkaA or gakkaB
                    num_str = rest.split('-')[1] if '-' in rest else ''
                    if num_str:
                        num = int(num_str)
                        key = f'{year}{part}'
                        data[key].append(num)

    print("=" * 60)
    print("データベースの実際の問題番号範囲")
    print("=" * 60)
    for key in sorted(data.keys()):
        nums = sorted(data[key])
        print(f'{key}: {len(nums):2d}問, No.{min(nums):02d}-{max(nums):02d}')
    print("=" * 60)

if __name__ == '__main__':
    main()
