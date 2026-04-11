#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
試験問題PDFから解答上の注意を抽出するスクリプト (pdfminer版)
"""
import os
import re
import sys

try:
    from pdfminer.high_level import extract_text
except ImportError:
    print("pdfminer.sixが必要です: pip install pdfminer.six")
    sys.exit(1)

def extract_first_page_text(pdf_path):
    """PDFの1ページ目のテキストを抽出"""
    try:
        # maxpages=1で1ページ目のみ抽出
        text = extract_text(pdf_path, page_numbers=[0])
        return text
    except Exception as e:
        print(f"Error reading {pdf_path}: {e}")
        return ""

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

            print(f"\n  {part_name}:")
            print("-" * 70)
            # 解答上の注意部分を抽出（【解答上の注意】から次のセクションまで）
            match = re.search(r'【解答上の注意】(.+?)(?:【|$)', text, re.DOTALL)
            if match:
                instructions = match.group(1).strip()
                # 問題番号の範囲と選択数を抜き出す
                lines = instructions.split('\n')
                for line in lines:
                    # No.1～No.15のようなパターンを含む行のみ表示
                    if 'No.' in line and ('問' in line or '全' in line or '選択' in line):
                        print(f"    {line.strip()}")
            else:
                print(f"    解答上の注意が見つかりません")
                # デバッグ用：最初の1000文字を表示
                print(f"    [デバッグ] 最初の1000文字:")
                print(f"    {text[:1000]}")

    print("\n" + "=" * 80)

if __name__ == '__main__':
    main()
