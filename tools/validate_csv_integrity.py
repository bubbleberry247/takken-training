#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""CSVの整合性を詳細チェック"""

import csv

csv_path = r"C:\ProgramData\Generative AI\Github\doboku-14w-training\tools\questionbank_drive_import.csv"

print("=== CSV整合性チェック ===\n")

# CSVを読み込み
with open(csv_path, 'r', encoding='utf-8-sig', newline='') as f:
    reader = csv.DictReader(f)
    fieldnames = reader.fieldnames
    rows = list(reader)

print(f"総行数: {len(rows)}")
print(f"カラム数: {len(fieldnames)}\n")

# 1. qIdの重複チェック
qids = [row['qId'] for row in rows]
duplicates = [qid for qid in set(qids) if qids.count(qid) > 1]

if duplicates:
    print(f"[WARNING] 重複しているqId: {len(duplicates)}件")
    for qid in duplicates[:5]:
        print(f"  - {qid}")
else:
    print("[OK] qIdの重複なし")

# 2. R3年度のデータチェック
r3_rows = [row for row in rows if row['qId'].startswith('R3')]
print(f"\nR3年度: {len(r3_rows)}件")
print(f"  R3gakkaA: {len([r for r in r3_rows if 'gakkaA' in r['qId']])}件")
print(f"  R3gakkaB: {len([r for r in r3_rows if 'gakkaB' in r['qId']])}件")

# 3. 必須フィールドの空欄チェック
required_fields = ['qId', 'segmentId', 'stem', 'choiceA', 'choiceB', 'choiceC', 'choiceD', 'correct']
empty_issues = []

for row in rows:
    for field in required_fields:
        if not row.get(field, '').strip():
            empty_issues.append(f"{row['qId']}: {field}が空欄")

if empty_issues:
    print(f"\n[WARNING] 必須フィールドの空欄: {len(empty_issues)}件")
    for issue in empty_issues[:10]:
        print(f"  - {issue}")
else:
    print("\n[OK] 必須フィールドに空欄なし")

# 4. R3年度の問題番号の連番チェック
print("\n=== R3年度の問題番号チェック ===")
for segment in ['R3gakkaA', 'R3gakkaB']:
    segment_rows = [r for r in rows if r['qId'].startswith(segment)]
    numbers = sorted([int(r['qId'].split('-')[1]) for r in segment_rows])

    missing = []
    for i in range(1, max(numbers) + 1):
        if i not in numbers:
            missing.append(i)

    if missing:
        print(f"[WARNING] {segment}: 欠番あり {missing}")
    else:
        print(f"[OK] {segment}: 1-{max(numbers)}まで連番")

# 5. CSVフォーマットチェック（カラム数）
with open(csv_path, 'r', encoding='utf-8-sig') as f:
    lines = f.readlines()
    header_cols = len(lines[0].strip().split(','))

    format_errors = []
    for i, line in enumerate(lines[1:], start=2):
        cols = len(line.strip().split(','))
        if cols != header_cols:
            qid = line.split(',')[0] if ',' in line else 'unknown'
            format_errors.append(f"行{i} ({qid}): {cols}カラム (期待値: {header_cols})")

    if format_errors:
        print(f"\n[WARNING] カラム数不一致: {len(format_errors)}件")
        for err in format_errors[:10]:
            print(f"  - {err}")
    else:
        print(f"\n[OK] すべての行のカラム数が一致")

print("\n=== チェック完了 ===")
