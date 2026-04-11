#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
試験問題PDFから解答上の注意を抽出するスクリプト
"""
import os
import re

try:
    import PyPDF2
except ImportError:
    print("PyPDF2が必要です: pip install PyPDF2")
    exit(1)

def extract_first_page_text(pdf_path):
    """PDFの1ページ目のテキストを抽出"""
    try:
        with open(pdf_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            if len(reader.pages) > 0:
                return reader.pages[0].extract_text()
    except Exception as e:
        print(f"Error reading {pdf_path}: {e}")
    return ""

def extract_exam_rules(text):
    """解答上の注意のテキストから問題範囲と選択数を抽出"""
    rules = []

    # パターン例: 【No.1】～【No.6】の6問題は、全問題を解答してください。
    # パターン例: 【No.7】～【No.15】の9問題のうちから、6問題を選択し、解答してください。

    # 全問解答パターン
    all_pattern = r'【No\.(\d+)】\s*～\s*【No\.(\d+)】\s*の\s*(\d+)\s*問題は、\s*全問題を解答'
    for match in re.finditer(all_pattern, text):
        no_from = int(match.group(1))
        no_to = int(match.group(2))
        total = int(match.group(3))
        rules.append({
            'range': f'No.{no_from}-{no_to}',
            'total': total,
            'required': total,
            'mode': 'ALL'
        })

    # 選択解答パターン
    pick_pattern = r'【No\.(\d+)】\s*～\s*【No\.(\d+)】\s*の\s*(\d+)\s*問題のうちから、\s*(\d+)\s*問題を選択'
    for match in re.finditer(pick_pattern, text):
        no_from = int(match.group(1))
        no_to = int(match.group(2))
        total = int(match.group(3))
        required = int(match.group(4))
        rules.append({
            'range': f'No.{no_from}-{no_to}',
            'total': total,
            'required': required,
            'mode': 'PICK'
        })

    return rules

def main():
    base_dir = r'C:\Users\masam\Desktop\KeyenceRK\１級土木施工管理技術検定愛一時検定_eラーニングサイト'

    years = ['R7', 'R6', 'R5', 'R4', 'R3', 'R2', 'R1']
    parts = [('gakkaA', '午前'), ('gakkaB', '午後')]

    print("=" * 80)
    print("試験問題PDFから解答上の注意を抽出")
    print("=" * 80)

    for year in years:
        print(f"\n### {year}年度")
        for part_code, part_name in parts:
            pdf_path = os.path.join(base_dir, f'{year}{part_code}_mondai.pdf')
            if not os.path.exists(pdf_path):
                print(f"  {part_name}: PDFファイルが見つかりません")
                continue

            text = extract_first_page_text(pdf_path)
            if not text:
                print(f"  {part_name}: テキスト抽出失敗")
                continue

            rules = extract_exam_rules(text)
            if not rules:
                print(f"  {part_name}: 解答上の注意が見つかりません")
                # デバッグ用：抽出したテキストの一部を表示
                print(f"    抽出テキスト（最初の500文字）:")
                print(f"    {text[:500]}")
                continue

            total_questions = sum(r['total'] for r in rules)
            total_required = sum(r['required'] for r in rules)

            print(f"  {part_name}: {total_questions}問中{total_required}問解答")
            for rule in rules:
                mode_str = "全問解答" if rule['mode'] == 'ALL' else f"{rule['total']}問中{rule['required']}問選択"
                print(f"    {rule['range']}: {mode_str}")

    print("\n" + "=" * 80)

if __name__ == '__main__':
    main()
