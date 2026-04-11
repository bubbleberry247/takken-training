#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
統合後のカバレッジを確認
"""

import sys
import io
import csv

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

with open('questionbank_drive_import.csv', 'r', encoding='utf-8-sig') as f:
    rows = list(csv.DictReader(f))

# 様々なパターンでカウント
completely_empty = 0  # 4つ全て空
partial = 0  # 1-3個のみ
all_filled = 0  # 4つ全て埋まっている

for row in rows:
    explain_a = row.get('explainA', '').strip()
    explain_b = row.get('explainB', '').strip()
    explain_c = row.get('explainC', '').strip()
    explain_d = row.get('explainD', '').strip()

    filled_count = sum([bool(explain_a), bool(explain_b), bool(explain_c), bool(explain_d)])

    if filled_count == 0:
        completely_empty += 1
    elif filled_count == 4:
        all_filled += 1
    else:
        partial += 1

print('='*80)
print('最新の説明文カバレッジ（統合後）')
print('='*80)
print(f'✅ 4つ全て揃っている:        {all_filled}問 ({all_filled/682*100:.1f}%)')
print(f'⚠️  一部のみ（1-3個）:        {partial}問 ({partial/682*100:.1f}%)')
print(f'❌ 完全に空（0個）:           {completely_empty}問 ({completely_empty/682*100:.1f}%)')
print('='*80)
print(f'合計: {all_filled + partial + completely_empty}問')
print()
print(f'📊 「未収集」の内訳:')
print(f'  - 完全に空（説明文が全くない）: {completely_empty}問')
print(f'  - 一部のみ（不完全）:          {partial}問')
print(f'  - 合計（4つ揃っていない）:     {completely_empty + partial}問')
