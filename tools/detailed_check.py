#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
問題文と説明文の状態を詳細確認
"""

import sys
import io
import csv

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# CSVを読み込み
with open('questionbank_drive_import.csv', 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    rows = list(reader)

print(f'総問題数: {len(rows)}問\n')

# 各フィールドの充填率をチェック
missing_stem = []
missing_choices = []
missing_explanations = []

for row in rows:
    qid = row.get('qId', '')

    # 問題文
    stem = row.get('stem', '').strip()
    if not stem:
        missing_stem.append(qid)

    # 選択肢
    choice_a = row.get('choiceA', '').strip()
    choice_b = row.get('choiceB', '').strip()
    choice_c = row.get('choiceC', '').strip()
    choice_d = row.get('choiceD', '').strip()

    if not (choice_a and choice_b and choice_c and choice_d):
        missing_choices.append(qid)

    # 説明文
    explain_a = row.get('explainA', '').strip()
    explain_b = row.get('explainB', '').strip()
    explain_c = row.get('explainC', '').strip()
    explain_d = row.get('explainD', '').strip()

    # 4つ全て空の場合のみカウント
    if not (explain_a or explain_b or explain_c or explain_d):
        missing_explanations.append(qid)

print('='*80)
print('データ完全性チェック')
print('='*80)
print(f"問題文（stem）が欠落:        {len(missing_stem)}問")
print(f"選択肢（A-D）が不完全:       {len(missing_choices)}問")
print(f"説明文（explainA-D）が全て空: {len(missing_explanations)}問")
print('='*80)

if missing_stem:
    print(f"\n❌ 問題文欠落リスト: {missing_stem[:10]}...")

if missing_choices:
    print(f"\n❌ 選択肢不完全リスト: {missing_choices[:10]}...")

if missing_explanations:
    print(f"\n📝 説明文が全て空のリスト（最初の20問）:")
    for i, qid in enumerate(missing_explanations[:20], 1):
        print(f"  {i}. {qid}")
    if len(missing_explanations) > 20:
        print(f"  ... 他 {len(missing_explanations) - 20}問")

# 年度別に集計
from collections import defaultdict
by_year = defaultdict(list)
for qid in missing_explanations:
    year_segment = qid.split('-')[0]  # R1gakkaA など
    by_year[year_segment].append(qid)

print(f"\n📊 説明文が全て空の問題（年度別）:")
for year_seg in sorted(by_year.keys()):
    print(f"  {year_seg}: {len(by_year[year_seg])}問")
