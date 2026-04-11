#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
説明文が不足している問題の詳細リストを出力
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
        # kakomonn.com用のIDを構築（CSV内のid列は存在しないため、URL生成が必要な場合は別途処理）
        # 今回はqIdのみ使用
        missing.append({
            'qId': qid,
            'year': row.get('year', ''),
            'segmentId': row.get('segmentId', ''),
            'stem': row.get('stem', '')[:50].replace('\n', ' '),  # 問題文の先頭50文字
        })

# 年度・セグメント別に集計
by_segment = defaultdict(list)
for item in missing:
    key = f"{item['year']}{item['segmentId']}"
    by_segment[key].append(item)

# 結果表示
print('# 説明文が不足している問題の詳細リスト\n')
print(f'**総数**: {len(missing)}問\n')

for segment in sorted(by_segment.keys()):
    items = by_segment[segment]
    print(f'\n## {segment} ({len(items)}問)\n')
    print('| No | qId | 問題文（抜粋） |')
    print('|----|-----|----------------|')
    for i, item in enumerate(items, 1):
        print(f"| {i} | {item['qId']} | {item['stem']}... |")

print('\n\n---\n')
print(f'合計: {len(missing)}問の説明文が不足しています。')
