#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数値欠落パターンの詳細調査

数値が欠落していると思われる箇所を検出
"""

import sys
import io
import csv
import re

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

CSV_FILE = r"C:\ProgramData\Generative AI\Github\doboku-14w-training\tools\questionbank_drive_import.csv"

def load_csv(filepath):
    """CSVファイルを読み込む"""
    rows = []
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows

def find_missing_numbers(text):
    """数値が欠落していると思われるパターンを検出"""
    findings = []

    # パターン1: スペース + 〜 + 数値 (前に数値がない)
    pattern1 = r'(?<![0-9])\s+[〜～]\s*(\d+)'
    matches = re.finditer(pattern1, text)
    for m in matches:
        findings.append({
            'pattern': 'スペース〜数値',
            'matched': m.group(),
            'context': text[max(0, m.start()-30):m.end()+20],
            'position': m.start(),
        })

    # パターン2: の / 以下 などの表現
    pattern2 = r'の\s*/\s*以[下上]'
    matches = re.finditer(pattern2, text)
    for m in matches:
        findings.append({
            'pattern': '分数欠落',
            'matched': m.group(),
            'context': text[max(0, m.start()-30):m.end()+20],
            'position': m.start(),
        })

    # パターン3: CBR が 未満
    pattern3 = r'(CBR|N値|含水比|密度|強度|厚さ)\s+(が|は)\s+未満'
    matches = re.finditer(pattern3, text)
    for m in matches:
        findings.append({
            'pattern': '数値+単位 が/は 未満',
            'matched': m.group(),
            'context': text[max(0, m.start()-30):m.end()+20],
            'position': m.start(),
        })

    # パターン4: 以下 でかつ
    pattern4 = r'(\d+)\s*(mm|cm|m|kg|t|%|°C)\s*以下\s*でかつ'
    matches = re.finditer(pattern4, text)
    for m in matches:
        findings.append({
            'pattern': '数値+単位 以下でかつ',
            'matched': m.group(),
            'context': text[max(0, m.start()-30):m.end()+30],
            'position': m.start(),
        })

    # パターン5: m 当たり 〜 (単位水量などの前に数値がない)
    pattern5 = r'm\s*当たり\s+[〜～]\s*(\d+)'
    matches = re.finditer(pattern5, text)
    for m in matches:
        findings.append({
            'pattern': 'm当たり〜数値',
            'matched': m.group(),
            'context': text[max(0, m.start()-30):m.end()+20],
            'position': m.start(),
        })

    # パターン6: 〜 % など (前に数値がない)
    pattern6 = r'(?<![0-9])\s+[〜～]\s*(\d+)\s*%'
    matches = re.finditer(pattern6, text)
    for m in matches:
        findings.append({
            'pattern': 'スペース〜数値%',
            'matched': m.group(),
            'context': text[max(0, m.start()-30):m.end()+20],
            'position': m.start(),
        })

    return findings

def analyze_csv(rows):
    """CSV全体を分析"""
    results = []

    text_columns = ['stem', 'choiceA', 'choiceB', 'choiceC', 'choiceD', 'choiceE',
                   'explainA', 'explainB', 'explainC', 'explainD', 'explainE',
                   'explainShort', 'explainLong']

    for idx, row in enumerate(rows, start=2):
        qid = row.get('qId', '')

        for col in text_columns:
            text = row.get(col, '')
            if not text:
                continue

            findings = find_missing_numbers(text)

            for finding in findings:
                results.append({
                    'row': idx,
                    'qId': qid,
                    'column': col,
                    'pattern': finding['pattern'],
                    'matched': finding['matched'],
                    'context': finding['context'].replace('\n', ' '),
                })

    return results

def main():
    print("=" * 80)
    print("数値欠落パターンの詳細調査")
    print("=" * 80)
    print()

    rows = load_csv(CSV_FILE)
    print(f"総問題数: {len(rows)}問")
    print()

    results = analyze_csv(rows)

    print(f"検出数: {len(results)}件")
    print()

    # パターン別にグループ化
    from collections import defaultdict
    by_pattern = defaultdict(list)
    for r in results:
        by_pattern[r['pattern']].append(r)

    for pattern in sorted(by_pattern.keys()):
        items = by_pattern[pattern]
        print(f"## {pattern} ({len(items)}件)")
        print()
        print("| 行番号 | qId | カラム | 検出箇所 | コンテキスト |")
        print("|--------|-----|--------|---------|-------------|")

        for item in items[:30]:  # 最大30件表示
            context = item['context'][:60]
            print(f"| {item['row']} | {item['qId']} | {item['column']} | {item['matched']} | {context}... |")

        if len(items) > 30:
            print(f"... 他 {len(items) - 30} 件")

        print()

if __name__ == "__main__":
    main()
