#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""R3gakkaB問題のstatusフィールドをチェック"""

import csv

csv_path = r"C:\ProgramData\Generative AI\Github\doboku-14w-training\tools\questionbank_drive_import.csv"

print("=== R3gakkaB status確認 ===\n")

with open(csv_path, 'r', encoding='utf-8-sig', newline='') as f:
    reader = csv.DictReader(f)
    rows = list(reader)

r3gakkaB_rows = [r for r in rows if r['qId'].startswith('R3gakkaB')]

print(f"R3gakkaB総数: {len(r3gakkaB_rows)}件\n")

status_counts = {}
status_examples = {}

for row in r3gakkaB_rows:
    status = row.get('status', '').strip()
    status_key = status if status else '(空欄)'

    if status_key not in status_counts:
        status_counts[status_key] = 0
        status_examples[status_key] = []

    status_counts[status_key] += 1
    if len(status_examples[status_key]) < 5:
        status_examples[status_key].append(row['qId'])

print("status別の件数:")
for status_key, count in status_counts.items():
    print(f"  {status_key}: {count}件")
    if count <= 5:
        print(f"    -> {', '.join(status_examples[status_key])}")
    else:
        print(f"    -> {', '.join(status_examples[status_key][:5])}...")

if 'published' in status_counts:
    print(f"\n[INFO] 'published'ステータス: {status_counts['published']}件")
    if status_counts['published'] < len(r3gakkaB_rows):
        print(f"[WARNING] {len(r3gakkaB_rows) - status_counts['published']}件が'published'以外のステータス")
        print("[ACTION] これらの問題はMockExam画面に表示されません")
else:
    print("\n[ERROR] 'published'ステータスの問題が0件！")
    print("[ACTION] すべてのR3gakkaB問題のstatusを'published'に修正する必要があります")
