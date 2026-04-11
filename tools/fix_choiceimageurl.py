#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
choiceImageUrlが誤って設定されている71件の問題を修正
テキスト選択肢を持つ問題では、choiceImageUrlを空欄にする
"""

import csv
from datetime import datetime
import shutil

csv_path = r"C:\ProgramData\Generative AI\Github\doboku-14w-training\tools\questionbank_drive_import.csv"
backup_path = csv_path.replace('.csv', f'_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv')

# 修正対象のqId（71件）
target_qids = [
    'R1gakkaB-003', 'R1gakkaB-012', 'R1gakkaB-014', 'R1gakkaB-028',
    'R2gakkaB-003', 'R2gakkaB-012', 'R2gakkaB-028',
    'R3gakkaB-003', 'R3gakkaB-006', 'R3gakkaB-015', 'R3gakkaB-021', 'R3gakkaB-022',
    'R3gakkaB-023', 'R3gakkaB-024', 'R3gakkaB-025', 'R3gakkaB-026', 'R3gakkaB-027',
    'R3gakkaB-028', 'R3gakkaB-029', 'R3gakkaB-030', 'R3gakkaB-032', 'R3gakkaB-033',
    'R3gakkaB-034', 'R3gakkaB-035',
    'R4gakkaA-001', 'R4gakkaB-003', 'R4gakkaB-006', 'R4gakkaB-021', 'R4gakkaB-022',
    'R4gakkaB-023', 'R4gakkaB-024', 'R4gakkaB-025', 'R4gakkaB-026', 'R4gakkaB-027',
    'R4gakkaB-028', 'R4gakkaB-029', 'R4gakkaB-030', 'R4gakkaB-031', 'R4gakkaB-032',
    'R4gakkaB-033', 'R4gakkaB-034', 'R4gakkaB-035',
    'R5gakkaA-020', 'R5gakkaB-003', 'R5gakkaB-006', 'R5gakkaB-021', 'R5gakkaB-023',
    'R5gakkaB-026', 'R5gakkaB-029', 'R5gakkaB-033',
    'R6gakkaA-001', 'R6gakkaA-002', 'R6gakkaA-003', 'R6gakkaA-004', 'R6gakkaA-005',
    'R6gakkaA-006', 'R6gakkaB-003', 'R6gakkaB-006', 'R6gakkaB-021', 'R6gakkaB-023',
    'R6gakkaB-026', 'R6gakkaB-029', 'R6gakkaB-033',
    'R7gakkaA-001', 'R7gakkaA-002', 'R7gakkaA-003', 'R7gakkaA-004', 'R7gakkaA-005',
    'R7gakkaA-025', 'R7gakkaB-003', 'R7gakkaB-006'
]

print(f"CSVファイルを読み込み中: {csv_path}")

# バックアップ作成
shutil.copy(csv_path, backup_path)
print(f"バックアップ作成: {backup_path}\n")

# CSVを読み込み
with open(csv_path, 'r', encoding='utf-8-sig', newline='') as f:
    reader = csv.DictReader(f)
    rows = list(reader)
    fieldnames = reader.fieldnames

print(f"総行数: {len(rows)}")
print(f"修正対象: {len(target_qids)}件\n")

fixed_count = 0

for row in rows:
    qid = row['qId']

    if qid in target_qids:
        original_url = row.get('choiceImageUrl', '')

        if original_url and original_url.strip() and original_url.strip() != '...':
            # choiceImageUrlを空欄にする
            row['choiceImageUrl'] = '...'
            fixed_count += 1
            print(f"[{fixed_count:2d}/71] {qid}: choiceImageUrl削除")

print(f"\n修正完了: {fixed_count}件")

# CSVを書き込み
with open(csv_path, 'w', encoding='utf-8-sig', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print(f"\n保存完了: {csv_path}")
print(f"バックアップ: {backup_path}")
