#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
説明文が不足している問題数を正確に検証
"""

import sys
import io
import csv
from collections import defaultdict

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# CSVを読み込み
with open('questionbank_drive_import.csv', 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    rows = list(reader)

print(f'総問題数: {len(rows)}問\n')

# 様々な基準でカウント
counts = {
    'total': len(rows),
    'all_four_empty': 0,  # 4つ全て空
    'all_four_filled': 0,  # 4つ全て埋まっている
    'partial_filled': 0,  # 一部だけ埋まっている
    'explainShort_filled': 0,  # explainShortがある
}

missing_all_four = []
missing_any = []

for row in rows:
    qid = row.get('qId', '')
    explain_a = row.get('explainA', '').strip()
    explain_b = row.get('explainB', '').strip()
    explain_c = row.get('explainC', '').strip()
    explain_d = row.get('explainD', '').strip()
    explain_short = row.get('explainShort', '').strip()

    filled_count = sum([bool(explain_a), bool(explain_b), bool(explain_c), bool(explain_d)])

    # 4つ全て空
    if filled_count == 0:
        counts['all_four_empty'] += 1
        missing_all_four.append(qid)
    # 4つ全て埋まっている
    elif filled_count == 4:
        counts['all_four_filled'] += 1
    # 一部だけ埋まっている
    else:
        counts['partial_filled'] += 1

    # 4つ全て埋まっていない（=不足）
    if filled_count < 4:
        missing_any.append(qid)

    # explainShortがある
    if explain_short:
        counts['explainShort_filled'] += 1

# 結果表示
print('='*80)
print('説明文カバレッジ統計')
print('='*80)
print(f"総問題数:                 {counts['total']}問")
print(f"explainShort あり:        {counts['explainShort_filled']}問 ({counts['explainShort_filled']/counts['total']*100:.1f}%)")
print(f"選択肢説明 4つ全て埋済:   {counts['all_four_filled']}問 ({counts['all_four_filled']/counts['total']*100:.1f}%)")
print(f"選択肢説明 一部のみ:      {counts['partial_filled']}問")
print(f"選択肢説明 4つ全て空:     {counts['all_four_empty']}問")
print('='*80)
print(f"\n📊 不足問題数")
print(f"  - 4つ全て空:            {counts['all_four_empty']}問 ← 完全に未収集")
print(f"  - 4つ未満（一部不足含）: {len(missing_any)}問 ← 収集が不完全")
print('='*80)

# handoff.mdとの照合
print("\n🔍 handoff.md との照合:")
print(f"  - handoff.md記載の選択肢説明（4つ全て）: 570問")
print(f"  - 実際のCSV（4つ全て埋済）:            {counts['all_four_filled']}問")
print(f"  - 差分:                                 {570 - counts['all_four_filled']}問")
print()
print(f"  - handoff.md記載のexplainShort:        546問")
print(f"  - 実際のCSV（explainShort あり）:      {counts['explainShort_filled']}問")
print(f"  - 差分:                                 {546 - counts['explainShort_filled']}問")
print()
print(f"  - handoff.md記載の残り収集対象:        131問")
print(f"  - 実際のCSV（4つ全て空）:              {counts['all_four_empty']}問")
print(f"  - 差分:                                 {counts['all_four_empty'] - 131}問")
