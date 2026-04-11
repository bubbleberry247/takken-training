#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
残存カンマ問題の修正
正規表現でカバーできなかった列挙中のカンマを修正
"""

import csv
import sys
import io

# UTF-8エンコーディング設定
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 修正対象を手動リスト化（レポートから特定）
FIXES = [
    {
        'qId': 'R1gakkaB-031',  # Row93（行番号93）
        'field': 'choiceD',
        'old': '径,かぶり',
        'new': '径、かぶり'
    },
    {
        'qId': 'R3gakkaA-002',  # Row195（行番号195）
        'field': 'choiceA',
        'old': '水,木質材料',
        'new': '水、木質材料'
    },
    {
        'qId': 'R3gakkaA-008',  # Row201（行番号201）
        'field': 'choiceB',
        'old': '壁,又は柱',
        'new': '壁、又は柱'
    },
    {
        'qId': 'R5gakkaA-002',  # Row387（行番号387）
        'field': 'choiceB',
        'old': '水,木質材料',
        'new': '水、木質材料'
    },
    {
        'qId': 'R7gakkaA-018',  # Row602（行番号602）
        'field': 'choiceA',
        'old': '土,油等',
        'new': '土、油等'
    },
    {
        'qId': 'R7gakkaA-022',  # Row606（行番号606）
        'field': 'choiceC',
        'old': '錆,塗料',
        'new': '錆、塗料'
    }
]

def fix_remaining_commas(input_path: str, output_path: str):
    """残存カンマの修正"""
    rows = []
    fix_count = 0

    with open(input_path, 'r', encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames

        for row in reader:
            qid = row.get('qId', '')

            # 該当するqIdの行を修正
            for fix in FIXES:
                if qid == fix['qId']:
                    field = fix['field']
                    if field in row and fix['old'] in row[field]:
                        old_value = row[field]
                        row[field] = row[field].replace(fix['old'], fix['new'])
                        print(f"✓ 修正: {qid} / {field}")
                        print(f"  旧: {old_value}")
                        print(f"  新: {row[field]}")
                        print()
                        fix_count += 1

            rows.append(row)

    # 出力
    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return fix_count

def main():
    input_path = 'C:/ProgramData/Generative AI/Github/doboku-14w-training/tools/questionbank_drive_import.csv'
    output_path = input_path

    print("=" * 60)
    print("残存カンマ問題の修正")
    print("=" * 60)
    print()

    fix_count = fix_remaining_commas(input_path, output_path)

    print("=" * 60)
    print(f"修正完了: {fix_count}件")
    print("=" * 60)

if __name__ == '__main__':
    main()
