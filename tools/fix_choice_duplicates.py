#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
選択肢の重複番号を削除するスクリプト

修正パターン:
1. ①①つ → ①つ (全角数字の重複)
2. ①①D13 → ①D13 (全角数字の重複)
3. （１）１つ → １つ (括弧付き数字の削除)
4. （１）D13 → D13 (括弧付き数字の削除)
"""
import sys
import io
import csv
import re

# UTF-8出力設定
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def fix_choice_text(text):
    """選択肢テキストの重複番号を修正"""
    if not text:
        return text, False

    original = text
    modified = False

    # パターン1: ①①, ②②, ③③, ④④ → ①, ②, ③, ④
    patterns = [
        (r'^①①', '①'),
        (r'^②②', '②'),
        (r'^③③', '③'),
        (r'^④④', '④'),
    ]

    for pattern, replacement in patterns:
        if re.match(pattern, text):
            text = re.sub(pattern, replacement, text)
            modified = True
            break

    # パターン2: （１）, （２）, （３）, （４） を削除
    patterns_paren = [
        (r'^（１）', ''),
        (r'^（２）', ''),
        (r'^（３）', ''),
        (r'^（４）', ''),
    ]

    for pattern, replacement in patterns_paren:
        if re.match(pattern, text):
            text = re.sub(pattern, replacement, text)
            modified = True
            break

    return text, modified

# CSVファイルを読み込み
input_file = r'C:\ProgramData\Generative AI\Github\doboku-14w-training\tools\questionbank_drive_import.csv'
output_file = r'C:\ProgramData\Generative AI\Github\doboku-14w-training\tools\questionbank_drive_import.csv'

rows = []
fixed_count = 0
fixed_questions = []

with open(input_file, 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    fieldnames = reader.fieldnames

    for row in reader:
        qid = row.get('qId', '').strip()
        modified = False

        # choiceA〜Eをチェック
        for choice_field in ['choiceA', 'choiceB', 'choiceC', 'choiceD', 'choiceE']:
            original = row.get(choice_field, '')
            fixed, success = fix_choice_text(original)

            if success:
                row[choice_field] = fixed
                modified = True
                print(f"{qid} {choice_field}: '{original}' → '{fixed}'")

        if modified:
            fixed_count += 1
            fixed_questions.append(qid)

        rows.append(row)

# 修正したデータを書き込み
with open(output_file, 'w', encoding='utf-8-sig', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print(f"\n処理完了:")
print(f"  - 修正した問題数: {fixed_count}問")
print(f"  - 問題ID: {', '.join(fixed_questions)}")
print(f"  - 合計: {len(rows)}問")
