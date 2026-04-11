#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
画像を使用している設問の問題文をチェック
図表の数値混入などの不要な文字列を検出
"""
import sys
import io
import csv
import re

# UTF-8出力設定
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 不要な文字列のパターン
suspicious_patterns = [
    (r'\d+[×xX]\d+[=＝]\d+', '計算式'),  # 4×250=1000のような計算式（全角・半角）
    (r'[D]\d+', '鉄筋番号'),  # D19, D22のような鉄筋番号
    (r'\d{4,}', '長い数字列'),  # 1900, 3800のような長い数字
    (r'([A-Zー\-]+)', '断面記号候補'),  # A-A, B-Bのような断面記号
]

# questionbank_drive_import.csvを読み込み
input_file = r'C:\ProgramData\Generative AI\Github\doboku-14w-training\tools\questionbank_drive_import.csv'

suspicious_questions = []

with open(input_file, 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)

    for idx, row in enumerate(reader, start=2):  # ヘッダーの次の行から
        image_url = row.get('imageUrl', '').strip()

        # 画像がある問題のみチェック
        if not image_url:
            continue

        question = row.get('stem', '')
        qid = row.get('qId', '')

        # 不要な文字列パターンをチェック
        found_patterns = []
        for pattern, name in suspicious_patterns:
            if re.search(pattern, question):
                matches = re.findall(pattern, question)
                found_patterns.append(f"{name}: {len(matches)}個")

        if found_patterns:
            suspicious_questions.append({
                'row': idx,
                'qId': qid,
                'patterns': ', '.join(found_patterns),
                'question_length': len(question)
            })

print(f"画像を使用している設問の不要文字列チェック")
print(f"=" * 70)
print()

if suspicious_questions:
    print(f"疑わしい問題: {len(suspicious_questions)}問")
    print()
    for item in suspicious_questions:
        print(f"行{item['row']}: {item['qId']}")
        print(f"  パターン: {item['patterns']}")
        print(f"  問題文の長さ: {item['question_length']}文字")
        print()
else:
    print("不要な文字列は検出されませんでした。")

print(f"=" * 70)
