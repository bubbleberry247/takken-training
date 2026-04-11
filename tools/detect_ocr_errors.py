#!/usr/bin/env python3
"""
OCR誤変換検出スクリプト

目的: questionbank_drive_import.csv 全682問のOCR誤変換を検出してレポート出力

検出パターン:
1. バッククォート文字 (`) を含むテキスト
2. 明らかな数値誤変換: bmm, cmm, dmm, emm, fmm, gmm, hmm など
3. 特殊パターン: ^m, ^cm, \層, 〜\, など
4. 数値の誤変換: = → 5, 8 → 1, 9 → 2 (文脈による検出)

出力: qId, フィールド名, 誤変換箇所をCSVレポート
"""

import csv
import re
import sys
import io
from datetime import datetime

# UTF-8標準出力
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 検出パターン定義
PATTERNS = {
    'backtick': r'`',  # バッククォート
    'x_mm': r'[a-z]mm',  # bmm, cmm, dmm など
    'caret_m': r'\^m|\^cm',  # ^m, ^cm
    'backslash_text': r'\\層|〜\\',  # \層, 〜\
    'suspicious_numbers': r'[0-9]+=|=[0-9]+',  # =が数値の代わり
}

def detect_errors(csv_path):
    """CSVファイルから誤変換を検出"""
    errors = []

    # フィールド名（検査対象）
    text_fields = [
        'stem',
        'choiceA', 'choiceB', 'choiceC', 'choiceD', 'choiceE',
        'explainA', 'explainB', 'explainC', 'explainD', 'explainE',
        'explainShort', 'explainLong'
    ]

    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)

        for row_num, row in enumerate(reader, start=2):  # ヘッダーを1行目として2行目から
            qid = row.get('qId', f'Row{row_num}')

            # 各フィールドをチェック
            for field in text_fields:
                text = row.get(field, '')
                if not text:
                    continue

                # パターンごとにチェック
                for pattern_name, pattern in PATTERNS.items():
                    matches = list(re.finditer(pattern, text))
                    if matches:
                        for match in matches:
                            # 前後のコンテキスト抽出（最大50文字）
                            start = max(0, match.start() - 25)
                            end = min(len(text), match.end() + 25)
                            context = text[start:end]

                            errors.append({
                                'qId': qid,
                                'field': field,
                                'pattern': pattern_name,
                                'matched_text': match.group(),
                                'context': context.replace('\n', ' ').replace(',', '、'),
                                'position': match.start()
                            })

    return errors

def generate_report(errors, output_path):
    """エラーレポートをCSV出力"""
    with open(output_path, 'w', encoding='utf-8-sig', newline='') as f:
        fieldnames = ['qId', 'field', 'pattern', 'matched_text', 'context', 'position']
        writer = csv.DictWriter(f, fieldnames=fieldnames)

        writer.writeheader()
        for error in errors:
            writer.writerow(error)

    print(f"\n✓ レポート出力完了: {output_path}")
    print(f"  検出件数: {len(errors)}件")

def print_summary(errors):
    """サマリー表示"""
    print("\n" + "="*80)
    print("OCR誤変換検出サマリー")
    print("="*80)

    # パターン別集計
    pattern_counts = {}
    for error in errors:
        pattern = error['pattern']
        pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1

    print("\n【パターン別検出数】")
    for pattern, count in sorted(pattern_counts.items(), key=lambda x: -x[1]):
        print(f"  {pattern:20s}: {count:3d}件")

    # qId別集計（上位10件）
    qid_counts = {}
    for error in errors:
        qid = error['qId']
        qid_counts[qid] = qid_counts.get(qid, 0) + 1

    print("\n【qId別検出数（上位10件）】")
    for qid, count in sorted(qid_counts.items(), key=lambda x: -x[1])[:10]:
        print(f"  {qid:20s}: {count:3d}件")

    # フィールド別集計
    field_counts = {}
    for error in errors:
        field = error['field']
        field_counts[field] = field_counts.get(field, 0) + 1

    print("\n【フィールド別検出数】")
    for field, count in sorted(field_counts.items(), key=lambda x: -x[1]):
        print(f"  {field:20s}: {count:3d}件")

    print("\n" + "="*80)

def main():
    csv_path = "C:/ProgramData/Generative AI/Github/doboku-14w-training/tools/questionbank_drive_import.csv"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = f"C:/ProgramData/Generative AI/Github/doboku-14w-training/tools/ocr_error_report_{timestamp}.csv"

    print(f"OCR誤変換検出開始...")
    print(f"対象ファイル: {csv_path}")

    # 検出実行
    errors = detect_errors(csv_path)

    # サマリー表示
    print_summary(errors)

    # レポート出力
    generate_report(errors, output_path)

    print(f"\n処理完了")

if __name__ == '__main__':
    main()
