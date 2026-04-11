#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
詳細OCR誤変換調査スクリプト

目的: QuestionBank CSVファイルのOCR誤変換を体系的に検出
"""

import sys
import io
import csv
import re
from collections import Counter, defaultdict

# UTF-8エンコーディング設定
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 調査対象CSVファイル
CSV_FILE = r"C:\ProgramData\Generative AI\Github\doboku-14w-training\tools\questionbank_drive_import.csv"

# OCR誤認識パターン定義
OCR_PATTERNS = {
    "漢字の誤認識": {
        "工/エ": [
            (r"エ事", "工事", "高"),
            (r"エ程", "工程", "高"),
            (r"エ法", "工法", "高"),
        ],
        "口/ロ": [
            (r"人ロ", "人口", "高"),
            (r"開ロ", "開口", "高"),
            (r"ロ径", "口径", "高"),
        ],
        "二/ニ": [
            (r"第ニ", "第二", "高"),
            (r"ニ次", "二次", "高"),
        ],
        "土/士": [
            (r"士木", "土木", "高"),
            (r"士質", "土質", "高"),
            (r"士砂", "土砂", "高"),
            (r"士壌", "土壌", "高"),
        ],
        "末/未": [
            (r"未端", "末端", "中"),
        ],
    },
    "カタカナの誤認識": {
        "長音符号": [
            (r"コンクリ一ト", "コンクリート", "高"),
            (r"セメント一", "セメント", "中"),
            (r"モルタ一ル", "モルタル", "中"),
        ],
        "ソ/ン": [
            (r"コソクリート", "コンクリート", "高"),
            (r"セソト", "セント", "中"),
        ],
    },
    "数字関連": {
        "チルダと数値": [
            (r"〜[0-9]+", "TILDE_NUM", "中"),  # 〜5 などの検出
        ],
        "欠落数値": [
            (r"\s[〜～]\s", "MISSING_NUM", "中"),  # スペース〜スペース
            (r"[のが]\s[〜～]\s", "MISSING_NUM", "中"),  # の 〜
        ],
    },
    "専門用語": {
        "締固め表記": [
            (r"締め固め", "締固め", "低"),  # 表記ゆれ
        ],
    },
    "句読点・記号": {
        "全角数字": [
            (r"[０-９]", "ZENKAKU_NUM", "高"),
        ],
        "不自然なスペース": [
            (r"\s{2,}", "MULTI_SPACE", "低"),
        ],
    },
}

def load_csv(filepath):
    """CSVファイルを読み込む"""
    rows = []
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows

def check_patterns(text, patterns):
    """テキスト内のパターンをチェック"""
    findings = []
    for category, subcategories in patterns.items():
        for subcategory, pattern_list in subcategories.items():
            for pattern_info in pattern_list:
                pattern = pattern_info[0]
                suggestion = pattern_info[1]
                confidence = pattern_info[2]

                matches = list(re.finditer(pattern, text))
                if matches:
                    for match in matches:
                        findings.append({
                            'category': category,
                            'subcategory': subcategory,
                            'pattern': pattern,
                            'matched': match.group(),
                            'suggestion': suggestion,
                            'confidence': confidence,
                            'position': match.start(),
                        })
    return findings

def analyze_csv(rows):
    """CSV全体を分析"""
    results = defaultdict(list)

    # 検査対象カラム
    text_columns = ['stem', 'choiceA', 'choiceB', 'choiceC', 'choiceD', 'choiceE',
                   'explainA', 'explainB', 'explainC', 'explainD', 'explainE',
                   'explainShort', 'explainLong']

    for idx, row in enumerate(rows, start=2):  # CSVの行番号は2から（ヘッダー行が1）
        qid = row.get('qId', '')

        for col in text_columns:
            text = row.get(col, '')
            if not text:
                continue

            findings = check_patterns(text, OCR_PATTERNS)

            for finding in findings:
                results[finding['category']].append({
                    'row': idx,
                    'qId': qid,
                    'column': col,
                    'matched': finding['matched'],
                    'suggestion': finding['suggestion'],
                    'confidence': finding['confidence'],
                    'subcategory': finding['subcategory'],
                    'context': text[max(0, finding['position']-20):finding['position']+30],
                })

    return results

def format_results(results):
    """結果を整形して出力"""
    print("=" * 80)
    print("詳細OCR誤変換調査結果")
    print("=" * 80)
    print()

    total_findings = 0

    for category in sorted(results.keys()):
        items = results[category]
        if not items:
            continue

        print(f"## {category}")
        print()

        # 確信度別にグループ化
        by_confidence = defaultdict(list)
        for item in items:
            by_confidence[item['confidence']].append(item)

        for confidence in ['高', '中', '低']:
            if confidence not in by_confidence:
                continue

            confidence_items = by_confidence[confidence]
            total_findings += len(confidence_items)

            print(f"### 確信度: {confidence} ({len(confidence_items)}件)")
            print()
            print("| 行番号 | qId | カラム | 誤認識箇所 | 修正案 | コンテキスト |")
            print("|--------|-----|--------|-----------|--------|--------------|")

            for item in confidence_items[:50]:  # 最大50件表示
                context = item['context'].replace('\n', ' ')[:40]
                print(f"| {item['row']} | {item['qId']} | {item['column']} | {item['matched']} | {item['suggestion']} | {context}... |")

            if len(confidence_items) > 50:
                print(f"... 他 {len(confidence_items) - 50} 件")

            print()

    print("=" * 80)
    print(f"合計検出数: {total_findings}件")
    print("=" * 80)

def main():
    print("CSVファイルを読み込み中...")
    rows = load_csv(CSV_FILE)
    print(f"総問題数: {len(rows)}問")
    print()

    print("OCR誤変換パターンを検索中...")
    results = analyze_csv(rows)
    print()

    format_results(results)

if __name__ == "__main__":
    main()
