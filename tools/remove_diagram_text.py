#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配筋図などの図表数値を問題文から削除するスクリプト
"""
import sys
import io
import csv
import re

# UTF-8出力設定
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def clean_stem(stem):
    """問題文から図表の数値部分を削除"""
    if not stem:
        return stem

    original_length = len(stem)

    # パターン1: 「どれか。」の後の文字列を削除
    # 問題文は通常「〜どれか。」で終わる
    patterns_to_split = [
        r'(どれか。)\s*.*',
        r'(どれか 。)\s*.*',
        r'(正しいものはどれか。)\s*.*',
        r'(適当なものはどれか。)\s*.*',
        r'(適当でないものはどれか。)\s*.*',
        r'(誤っているものはどれか。)\s*.*',
    ]

    for pattern in patterns_to_split:
        match = re.search(pattern, stem)
        if match:
            # マッチした部分の終わりまでを保持
            stem = stem[:match.end(1)]
            break

    # 削除された文字数
    removed_length = original_length - len(stem)

    return stem, removed_length

# questionbank_drive_import.csvを読み込み、修正
input_file = r'C:\ProgramData\Generative AI\Github\doboku-14w-training\tools\questionbank_drive_import.csv'
output_file = r'C:\ProgramData\Generative AI\Github\doboku-14w-training\tools\questionbank_drive_import.csv'

rows = []
cleaned_count = 0
total_removed = 0

with open(input_file, 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    fieldnames = reader.fieldnames

    for row in reader:
        image_url = row.get('imageUrl', '').strip()
        stem = row.get('stem', '')

        # 画像がある問題のみ処理
        if image_url and stem:
            cleaned_stem, removed = clean_stem(stem)

            if removed > 0:
                row['stem'] = cleaned_stem
                cleaned_count += 1
                total_removed += removed
                print(f"{row.get('qId', '')}: {removed}文字削除")

        rows.append(row)

# 修正したデータを書き込み
with open(output_file, 'w', encoding='utf-8-sig', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print(f"\n処理完了:")
print(f"  - 修正した問題数: {cleaned_count}問")
print(f"  - 削除した文字数合計: {total_removed}文字")
print(f"  - 合計: {len(rows)}問")
