#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
問題文の体裁を整える総合スクリプト:
1. R7gakkaA-025のchoiceA先頭「2 」削除
2. 「O つ」「Oつ」→「4つ」に修正
3. 問題文の番号（1, 2, 3, 4）を改行して文頭に配置
"""

import csv
import re
from datetime import datetime
import shutil

csv_path = r"C:\ProgramData\Generative AI\Github\doboku-14w-training\tools\questionbank_drive_import.csv"
backup_path = csv_path.replace('.csv', f'_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv')

print(f"CSVファイルを読み込み中: {csv_path}")

# バックアップ作成
shutil.copy(csv_path, backup_path)
print(f"バックアップ作成: {backup_path}\n")

# CSVを読み込み
with open(csv_path, 'r', encoding='utf-8-sig', newline='') as f:
    reader = csv.DictReader(f)
    rows = list(reader)
    fieldnames = reader.fieldnames

print(f"総行数: {len(rows)}\n")

# 統計
fix1_count = 0  # R7gakkaA-025のchoiceA修正
fix2_count = 0  # 「O つ」修正
fix3_count = 0  # 番号改行

for row in rows:
    qid = row['qId']

    # 1. R7gakkaA-025のchoiceA先頭「2 」削除
    if qid == 'R7gakkaA-025':
        choice_a = row.get('choiceA', '')
        if choice_a.startswith('2 '):
            row['choiceA'] = choice_a[2:]  # 先頭2文字削除
            fix1_count += 1
            print(f"[修正1] {qid}: choiceA先頭「2 」削除")

    # 2. stemの「O つ」「Oつ」→「4つ」修正
    stem = row['stem']
    original_stem = stem

    # 「O つ」「Oつ」→「4つ」（半角O、全角O両方対応）
    stem = re.sub(r'[OＯo][\s　]*つ', '4つ', stem)

    if stem != original_stem:
        fix2_count += 1
        print(f"[修正2] {qid}: 「O つ」→「4つ」修正")

    # 3. 問題文の番号を改行して文頭に配置
    # パターン: 「。1」「。 1」→「。\n1」（句点の後に番号がある場合）
    # ただし、「1〜4」「1～4」のような範囲表記は改行しない
    # 条件: 「。」の後に「1」「2」「3」「4」が続く場合のみ改行

    # まず、既に改行されている場合はスキップ（既に正しい形式）
    # 「。1」「。 1」→「。\n1」に修正
    new_stem = re.sub(r'([。])[\s　]*([1234])(?![〜～\-0-9])', r'\1\n\2', stem)

    if new_stem != stem:
        stem = new_stem
        fix3_count += 1
        print(f"[修正3] {qid}: 番号を改行")

    row['stem'] = stem

print(f"\n=== 修正統計 ===")
print(f"R7gakkaA-025のchoiceA修正: {fix1_count}件")
print(f"「O つ」修正: {fix2_count}件")
print(f"番号改行: {fix3_count}件")

# CSVを書き込み
with open(csv_path, 'w', encoding='utf-8-sig', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print(f"\n保存完了: {csv_path}")
print(f"バックアップ: {backup_path}")
