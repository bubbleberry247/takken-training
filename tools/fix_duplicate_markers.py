#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
選択肢の重複マーカーを修正するスクリプト
(イ)(イ)塑性限界  (ロ)...  (ハ)(ロ)液性限界  (ニ)...  (ハ)液性指数
↓
①（イ）塑性限界　（ロ）液性限界　（ハ）液性指数
"""
import sys
import io
import csv
import re

# UTF-8出力設定
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def fix_choice_format(text):
    """選択肢のフォーマットを修正"""
    if not text or '(イ)' not in text:
        return text, False

    original = text

    # パターン: (イ)(イ)語句1  (ロ)...  (ハ)(ロ)語句2  (ニ)...  (ハ)語句3
    # → （イ）語句1　（ロ）語句2　（ハ）語句3

    # ステップ1: (イ)(イ) → (イ)
    text = text.replace('(イ)(イ)', '(イ)')

    # ステップ2: (ロ)...  (ハ)(ロ) → (ロ) を抽出
    # まず、(イ)の後の語句を抽出
    parts = []

    # (イ)語句 を抽出
    match_i = re.search(r'\(イ\)([^\(]+)', text)
    if match_i:
        parts.append(('イ', match_i.group(1).strip()))

    # (ハ)(ロ)語句 を抽出 → (ロ)語句
    match_ro = re.search(r'\(ハ\)\(ロ\)([^\(]+)', text)
    if match_ro:
        parts.append(('ロ', match_ro.group(1).strip()))

    # 最後の (ハ)語句 を抽出
    # (ニ)...  (ハ)語句 のパターン
    match_ha = re.search(r'\(ニ\)[^(]*\(ハ\)(.+)$', text)
    if match_ha:
        parts.append(('ハ', match_ha.group(1).strip()))

    if len(parts) == 3:
        # 成功: （イ）語句1　（ロ）語句2　（ハ）語句3 の形式に整形
        formatted = '　'.join([f'（{marker}）{word}' for marker, word in parts])
        return formatted, True

    # パターンマッチ失敗の場合は元のまま
    return original, False

# questionbank_drive_import.csvを読み込み
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

        # choiceA〜Dをチェック
        for choice_field in ['choiceA', 'choiceB', 'choiceC', 'choiceD']:
            original = row.get(choice_field, '')
            fixed, success = fix_choice_format(original)

            if success:
                row[choice_field] = fixed
                modified = True

        if modified:
            fixed_count += 1
            fixed_questions.append(qid)
            print(f"{qid}: 選択肢フォーマット修正")

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
