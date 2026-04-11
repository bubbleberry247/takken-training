#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import csv
import re

def fix_choice(choice):
    if not choice:
        return choice

    print(f"Original: {choice}")
    print(f"Contains (イ)R: {'(イ)R' in choice}")
    print(f"Contains （イ）R: {'（イ）R' in choice}")
    print()

    # 全角括弧を半角に変換
    choice = choice.replace('（イ）', '(イ)')
    choice = choice.replace('（ロ）', '(ロ)')
    choice = choice.replace('（ハ）', '(ハ)')
    choice = choice.replace('（ニ）', '(ニ)')

    print(f"After conversion: {choice}")
    print(f"Now contains (イ)R: {'(イ)R' in choice}")
    print()

    # 誤変換された Q, R, S, T を削除
    choice = re.sub(r'\(イ\)[QRST](?=\()', '(イ)', choice)
    choice = re.sub(r'\(ロ\)[QRST](?=\()', '(ロ)', choice)
    choice = re.sub(r'\(ハ\)[QRST](?=\()', '(ハ)', choice)
    choice = re.sub(r'\(ニ\)[QRST](?=\()', '(ニ)', choice)

    print(f"After QRST removal: {choice}")
    print()

    # スペース追加
    choice = re.sub(r'\(イ\)', '(イ)  ', choice)
    choice = re.sub(r'\(ロ\)', '(ロ)  ', choice)
    choice = re.sub(r'\(ハ\)', '(ハ)  ', choice)
    choice = re.sub(r'\(ニ\)', '(ニ)  ', choice)

    choice = re.sub(r'\s{3,}', '  ', choice)
    choice = choice.strip()

    print(f"Final: {choice}")

    return choice


with open('questionbank_drive_import.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    rows = list(reader)

    # 472行目（0-indexed で470）
    row = rows[470]
    print("=" * 60)
    print(f"Row 472: {row['qId']}")
    print("=" * 60)
    print()

    result = fix_choice(row['choiceA'])
