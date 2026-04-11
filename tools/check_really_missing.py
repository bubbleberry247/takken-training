#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
本当に何も説明文がない問題を確認
"""

import sys
import io
import csv

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# CSVを読み込み
with open('questionbank_drive_import.csv', 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    rows = list(reader)

# 様々なパターンでカウント
completely_empty = []  # 全ての説明文が空
explain_short_only = []  # explainShortのみ
explain_abcd_only = []  # explainA-Dのみ
both_filled = []  # 両方あり

for row in rows:
    qid = row.get('qId', '')
    explain_a = row.get('explainA', '').strip()
    explain_b = row.get('explainB', '').strip()
    explain_c = row.get('explainC', '').strip()
    explain_d = row.get('explainD', '').strip()
    explain_short = row.get('explainShort', '').strip()

    has_abcd = bool(explain_a or explain_b or explain_c or explain_d)
    has_short = bool(explain_short)

    if not has_abcd and not has_short:
        completely_empty.append(qid)
    elif has_short and not has_abcd:
        explain_short_only.append(qid)
    elif has_abcd and not has_short:
        explain_abcd_only.append(qid)
    else:
        both_filled.append(qid)

print('='*80)
print('説明文の状態別カウント')
print('='*80)
print(f"1. 完全に空（explainShort も explainA-D も無し）: {len(completely_empty)}問")
print(f"2. explainShort のみ（統合解説形式）:           {len(explain_short_only)}問")
print(f"3. explainA-D のみ（選択肢別のみ）:             {len(explain_abcd_only)}問")
print(f"4. 両方あり（理想的）:                          {len(both_filled)}問")
print('='*80)
print(f"合計: {len(completely_empty) + len(explain_short_only) + len(explain_abcd_only) + len(both_filled)}問")

if completely_empty:
    print(f"\n❌ 完全に空のリスト（最初の30問）:")
    for i, qid in enumerate(completely_empty[:30], 1):
        print(f"  {i}. {qid}")
    if len(completely_empty) > 30:
        print(f"  ... 他 {len(completely_empty) - 30}問")

if explain_short_only:
    print(f"\n⚠️ explainShortのみ（統合解説形式）の問題（最初の10問）:")
    for i, qid in enumerate(explain_short_only[:10], 1):
        print(f"  {i}. {qid}")
    print(f"  ... 計 {len(explain_short_only)}問")
