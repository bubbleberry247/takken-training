#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
穴埋め問題の問題文（stem）から余分な選択肢テキストを削除し、
「R〜S」を「（イ）〜（ニ）」に修正するスクリプト
"""

import csv
import re
from datetime import datetime

csv_path = r"C:\ProgramData\Generative AI\Github\doboku-14w-training\tools\questionbank_drive_import.csv"
backup_path = csv_path.replace('.csv', f'_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv')
output_path = csv_path

print(f"CSVファイルを読み込み中: {csv_path}")

# バックアップ作成
import shutil
shutil.copy(csv_path, backup_path)
print(f"バックアップ作成: {backup_path}")

# CSVを読み込み
with open(csv_path, 'r', encoding='utf-8-sig', newline='') as f:
    reader = csv.DictReader(f)
    rows = list(reader)
    fieldnames = reader.fieldnames

print(f"総行数: {len(rows)}")

# 修正対象の問題リスト（fix_manual_list.csvから）
target_qids = [
    'R3gakkaB-021', 'R3gakkaB-022', 'R3gakkaB-023', 'R3gakkaB-024', 'R3gakkaB-025',
    'R3gakkaB-026', 'R3gakkaB-027', 'R3gakkaB-028', 'R3gakkaB-029', 'R3gakkaB-030',
    'R3gakkaB-031', 'R3gakkaB-032', 'R3gakkaB-033', 'R3gakkaB-034', 'R3gakkaB-035',
    'R4gakkaB-021', 'R4gakkaB-022', 'R4gakkaB-023', 'R4gakkaB-024', 'R4gakkaB-025',
    'R4gakkaB-026', 'R4gakkaB-027', 'R4gakkaB-028', 'R4gakkaB-029', 'R4gakkaB-030',
    'R4gakkaB-031', 'R4gakkaB-032', 'R4gakkaB-033', 'R4gakkaB-034', 'R4gakkaB-035',
    'R5gakkaB-021', 'R5gakkaB-023', 'R5gakkaB-026', 'R5gakkaB-029', 'R5gakkaB-033',
    'R6gakkaB-021', 'R6gakkaB-023', 'R6gakkaB-026', 'R6gakkaB-029', 'R6gakkaB-033'
]

fixed_count = 0

for row in rows:
    qid = row['qId']

    if qid not in target_qids:
        continue

    stem = row['stem']
    original_stem = stem

    # 1. 「R〜S」「Q〜S」などを「（イ）〜（ニ）」に修正
    stem = re.sub(r'[RQ]〜[ST]', '（イ）〜（ニ）', stem)
    stem = re.sub(r'[RQ]～[ST]', '（イ）〜（ニ）', stem)

    # 2. 選択肢部分を削除（(イ) (ロ) (ハ) (ニ) から始まる部分以降を削除）
    # パターン: 改行後に「(イ) (ロ) (ハ) (ニ)」が続く行以降を削除
    match = re.search(r'\n\s*\(イ\)\s*\(ロ\)\s*\(ハ\)\s*\(ニ\)', stem)
    if match:
        stem = stem[:match.start()].rstrip()

    # 3. 箇条書き部分の整形（既に改行されているはずだが念のため確認）
    # 「・常時に」「・一定の」「・事業者は」で始まる行が改行されていることを確認
    # （今回は削除のみで整形は不要のようなので省略）

    if stem != original_stem:
        row['stem'] = stem
        fixed_count += 1
        print(f"[OK] Fixed: {qid}")
        print(f"     Before: {len(original_stem)} chars")
        print(f"     After:  {len(stem)} chars")

print(f"\n修正した問題数: {fixed_count}")

# CSVを書き込み
with open(output_path, 'w', encoding='utf-8-sig', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print(f"\n修正完了: {output_path}")
print(f"バックアップ: {backup_path}")
