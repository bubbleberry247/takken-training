#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
説明文が空の問題のサンプル表示
"""

import sys
import io
import csv

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# CSVを読み込み
with open('questionbank_drive_import.csv', 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    rows = list(reader)

# 説明文が全て空の問題を抽出
missing = []
for row in rows:
    qid = row.get('qId', '')
    explain_a = row.get('explainA', '').strip()
    explain_b = row.get('explainB', '').strip()
    explain_c = row.get('explainC', '').strip()
    explain_d = row.get('explainD', '').strip()

    if not (explain_a or explain_b or explain_c or explain_d):
        missing.append({
            'qId': qid,
            'stem': row.get('stem', '')[:60],
            'explainA': explain_a,
            'explainB': explain_b,
            'explainC': explain_c,
            'explainD': explain_d,
            'explainShort': row.get('explainShort', '').strip(),
        })

# 最初の5問をサンプル表示
print(f'説明文が全て空の問題: {len(missing)}問\n')
print('='*80)
print('サンプル（最初の5問）:')
print('='*80)
for i, item in enumerate(missing[:5], 1):
    print(f"\n{i}. {item['qId']}")
    print(f"   問題文: {item['stem']}...")
    print(f"   explainA: '{item['explainA']}'")
    print(f"   explainB: '{item['explainB']}'")
    print(f"   explainC: '{item['explainC']}'")
    print(f"   explainD: '{item['explainD']}'")
    print(f"   explainShort: '{item['explainShort']}'")

# 逆に、説明文が揃っている問題もサンプル表示
filled = []
for row in rows:
    qid = row.get('qId', '')
    explain_a = row.get('explainA', '').strip()
    explain_b = row.get('explainB', '').strip()
    explain_c = row.get('explainC', '').strip()
    explain_d = row.get('explainD', '').strip()

    if explain_a and explain_b and explain_c and explain_d:
        filled.append(qid)

print(f'\n\n説明文が4つ全て揃っている問題: {len(filled)}問')
print(f'説明文が空またはnullの問題: {len(missing)}問')
print(f'合計: {len(filled) + len(missing)}問（一部のみ埋まっている問題: {len(rows) - len(filled) - len(missing)}問）')
