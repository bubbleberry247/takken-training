#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
選択肢番号を①②③④に統一するスクリプト
"""
import sys
import io
import csv
import re

# UTF-8出力設定
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def normalize_choice_text(text):
    """選択肢のテキストを正規化"""
    if not text:
        return text

    # （１）（２）（３）（４）→ ①②③④
    text = text.replace('（１）', '①')
    text = text.replace('（２）', '②')
    text = text.replace('（３）', '③')
    text = text.replace('（４）', '④')

    # 「1と2」のようなパターン → 「①と②」
    text = re.sub(r'(\d)と(\d)', lambda m: f"{'①②③④'[int(m.group(1))-1]}と{'①②③④'[int(m.group(2))-1]}", text)

    # 「１つ」「２つ」→ 「①つ」「②つ」
    text = text.replace('１つ', '①つ')
    text = text.replace('２つ', '②つ')
    text = text.replace('３つ', '③つ')
    text = text.replace('４つ', '④つ')

    return text

# questionbank_drive_import.csvを読み込み、修正
input_file = r'C:\ProgramData\Generative AI\Github\doboku-14w-training\tools\questionbank_drive_import.csv'
output_file = r'C:\ProgramData\Generative AI\Github\doboku-14w-training\tools\questionbank_drive_import.csv'

rows = []
modified_count = 0

with open(input_file, 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    fieldnames = reader.fieldnames

    for row in reader:
        modified = False

        # choiceA, choiceB, choiceC, choiceDを正規化
        for choice_field in ['choiceA', 'choiceB', 'choiceC', 'choiceD']:
            original = row.get(choice_field, '')
            normalized = normalize_choice_text(original)
            if original != normalized:
                row[choice_field] = normalized
                modified = True

        if modified:
            modified_count += 1

        rows.append(row)

# 修正したデータを書き込み
with open(output_file, 'w', encoding='utf-8-sig', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print(f"処理完了:")
print(f"  - 修正した問題数: {modified_count}問")
print(f"  - 合計: {len(rows)}問")
