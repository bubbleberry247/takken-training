#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""R3gakkaB問題がisValidChoiceQuestion_()の条件を満たすか検証"""

import csv
import re

csv_path = r"C:\ProgramData\Generative AI\Github\doboku-14w-training\tools\questionbank_drive_import.csv"

print("=== R3gakkaB isValidChoiceQuestion_() 検証 ===\n")

def is_blank(v):
    return str(v).strip() == ''

def validate_question(row):
    """isValidChoiceQuestion_()のロジックを再現"""
    errors = []

    # 1. choiceA-Dが空欄でないか
    for choice in ['choiceA', 'choiceB', 'choiceC', 'choiceD']:
        if is_blank(row.get(choice, '')):
            errors.append(f"{choice}が空欄")

    # 2. correctフィールドが空欄でないか
    correct = row.get('correct', '').strip().upper()
    if not correct:
        errors.append("correctが空欄")
        return errors

    # 3. correctのフォーマットチェック
    choiceE = row.get('choiceE', '').strip()
    has_e = bool(choiceE)

    parts = [p.strip() for p in correct.split(',') if p.strip()]
    if not parts:
        errors.append("correctが空（カンマのみ）")
        return errors

    for part in parts:
        if has_e:
            if not re.match(r'^[A-E]$', part):
                errors.append(f"correct '{part}' がA-E形式でない")
        else:
            if not re.match(r'^[A-D]$', part):
                errors.append(f"correct '{part}' がA-D形式でない")

    # 4. correctで指定された選択肢が実際に存在するか
    choice_map = {
        'A': row.get('choiceA', '').strip(),
        'B': row.get('choiceB', '').strip(),
        'C': row.get('choiceC', '').strip(),
        'D': row.get('choiceD', '').strip(),
        'E': row.get('choiceE', '').strip()
    }

    for part in parts:
        if is_blank(choice_map.get(part, '')):
            errors.append(f"correct '{part}' で指定された選択肢が空欄")

    return errors

with open(csv_path, 'r', encoding='utf-8-sig', newline='') as f:
    reader = csv.DictReader(f)
    rows = list(reader)

r3gakkaB_rows = [r for r in rows if r['qId'].startswith('R3gakkaB')]

print(f"R3gakkaB総数: {len(r3gakkaB_rows)}件\n")

invalid_count = 0
invalid_questions = []

for row in r3gakkaB_rows:
    errors = validate_question(row)
    if errors:
        invalid_count += 1
        invalid_questions.append({
            'qId': row['qId'],
            'errors': errors
        })

if invalid_count == 0:
    print("[OK] すべてのR3gakkaB問題がisValidChoiceQuestion_()の条件を満たしています")
    print("→ 別の原因を調査する必要があります")
else:
    print(f"[ERROR] {invalid_count}件のR3gakkaB問題が検証に失敗\n")
    print("詳細:")
    for item in invalid_questions[:10]:
        print(f"\n{item['qId']}:")
        for err in item['errors']:
            print(f"  - {err}")

    if len(invalid_questions) > 10:
        print(f"\n... 他 {len(invalid_questions) - 10}件")

    print(f"\n[ACTION] これらの問題を修正する必要があります")
    print("         CSVの該当行を確認し、choiceA-D, correctフィールドを修正してください")

print("\n=== 検証完了 ===")
