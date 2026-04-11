#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
説明文が不足している問題を特定する
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

# 説明文が不足している問題を抽出
missing = []
for row in rows:
    qid = row.get('qId', '')
    explain_a = row.get('explainA', '').strip()
    explain_b = row.get('explainB', '').strip()
    explain_c = row.get('explainC', '').strip()
    explain_d = row.get('explainD', '').strip()

    # 4つ全て空の場合のみ「不足」とみなす
    if not (explain_a or explain_b or explain_c or explain_d):
        missing.append({
            'qId': qid,
            'year': row.get('year', ''),
            'segmentId': row.get('segmentId', ''),
        })

# 年度・セグメント別に集計
by_segment = defaultdict(list)
for item in missing:
    key = f"{item['year']}{item['segmentId']}"
    by_segment[key].append(item['qId'])

# 結果表示
print(f'説明文が不足している問題: {len(missing)}問\n')
for segment in sorted(by_segment.keys()):
    qids = by_segment[segment]
    print(f'{segment}: {len(qids)}問')
    print(f'  範囲: {qids[0]} 〜 {qids[-1]}')
    print()
