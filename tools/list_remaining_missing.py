#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
残りの未収集問題の詳細リストを出力
"""

import sys
import io
import csv
from collections import defaultdict

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

with open('questionbank_drive_import.csv', 'r', encoding='utf-8-sig') as f:
    rows = list(csv.DictReader(f))

# 未収集問題を分類
completely_empty = []  # 4つ全て空
partial = []  # 1-3個のみ

for row in rows:
    qid = row.get('qId', '')
    explain_a = row.get('explainA', '').strip()
    explain_b = row.get('explainB', '').strip()
    explain_c = row.get('explainC', '').strip()
    explain_d = row.get('explainD', '').strip()

    filled_count = sum([bool(explain_a), bool(explain_b), bool(explain_c), bool(explain_d)])

    if filled_count == 0:
        completely_empty.append({
            'qId': qid,
            'year': row.get('year', ''),
            'segmentId': row.get('segmentId', ''),
            'stem': row.get('stem', '')[:50],
        })
    elif 0 < filled_count < 4:
        partial.append({
            'qId': qid,
            'year': row.get('year', ''),
            'segmentId': row.get('segmentId', ''),
            'filled': filled_count,
            'explainA': '✅' if explain_a else '❌',
            'explainB': '✅' if explain_b else '❌',
            'explainC': '✅' if explain_c else '❌',
            'explainD': '✅' if explain_d else '❌',
        })

# 年度・セグメント別に集計
def group_by_segment(items):
    by_segment = defaultdict(list)
    for item in items:
        key = f"{item['year']}{item['segmentId']}"
        by_segment[key].append(item['qId'])
    return by_segment

empty_by_segment = group_by_segment(completely_empty)
partial_by_segment = group_by_segment(partial)

print('='*80)
print('❌ 完全に空（説明文が全くない）: 138問')
print('='*80)

for segment in sorted(empty_by_segment.keys()):
    qids = empty_by_segment[segment]
    print(f'\n{segment}: {len(qids)}問')
    print(f'範囲: {qids[0]} 〜 {qids[-1]}')
    print('qIdリスト:')
    # 10問ずつ改行
    for i in range(0, len(qids), 10):
        chunk = qids[i:i+10]
        print(f'  {", ".join(chunk)}')

print('\n\n')
print('='*80)
print('⚠️ 一部のみ（不完全）: 17問')
print('='*80)

if partial:
    print('\n| No | qId | A | B | C | D | 不足数 |')
    print('|----|-----|---|---|---|---|----|')
    for i, item in enumerate(partial, 1):
        missing = 4 - item['filled']
        print(f"| {i} | {item['qId']} | {item['explainA']} | {item['explainB']} | {item['explainC']} | {item['explainD']} | {missing}個 |")

print('\n\n')
print('='*80)
print('サマリー')
print('='*80)
print(f'完全に空:   {len(completely_empty)}問')
print(f'一部のみ:   {len(partial)}問')
print(f'合計:       {len(completely_empty) + len(partial)}問')
