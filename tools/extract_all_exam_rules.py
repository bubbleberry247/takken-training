#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
DOCXファイルから全年度の解答上の注意を抽出
"""
import os
import re
import docx

def extract_exam_rules_from_docx(docx_path):
    """DOCXから解答上の注意を抽出"""
    try:
        doc = docx.Document(docx_path)

        # 最初の30段落から解答上の注意を探す
        text_lines = []
        for para in doc.paragraphs[:40]:
            text = para.text.strip()
            if text:
                text_lines.append(text)

        full_text = '\n'.join(text_lines)

        # No.○～No.○ のパターンを抽出
        rules = []

        # パターン1: No. X～No. Yは全問解答
        all_pattern = r'No\.\s*(\d+)\s*[～~〜]\s*No\.\s*(\d+)\s*[はﾊ].*?全[問\?]'
        for match in re.finditer(all_pattern, full_text):
            no_from = int(match.group(1))
            no_to = int(match.group(2))
            total = no_to - no_from + 1
            rules.append({
                'range': f'No.{no_from}-{no_to}',
                'no_from': no_from,
                'no_to': no_to,
                'total': total,
                'required': total,
                'mode': 'ALL'
            })

        # パターン2: No. X～No. Yのうち○問解答
        pick_pattern = r'No\.\s*(\d+)\s*[～~〜]\s*No\.\s*(\d+)\s*[のﾉ].*?(\d+)\s*[問\?][をｦ]?[解\?][答\?]'
        for match in re.finditer(pick_pattern, full_text):
            no_from = int(match.group(1))
            no_to = int(match.group(2))
            required = int(match.group(3))
            total = no_to - no_from + 1

            # 既に同じ範囲が全問解答として登録されていないかチェック
            if not any(r['no_from'] == no_from and r['no_to'] == no_to and r['mode'] == 'ALL' for r in rules):
                rules.append({
                    'range': f'No.{no_from}-{no_to}',
                    'no_from': no_from,
                    'no_to': no_to,
                    'total': total,
                    'required': required,
                    'mode': 'PICK'
                })

        # 問題番号順にソート
        rules.sort(key=lambda x: x['no_from'])

        return rules

    except Exception as e:
        print(f"Error: {e}")
        return []

def main():
    base_dir = r'C:\Users\masam\Desktop\KeyenceRK\１級土木施工管理技術検定愛一時検定_eラーニングサイト\docx_out'

    years = ['R7', 'R6', 'R5', 'R4', 'R3', 'R2', 'R1']
    parts = [('gakkaA', '午前'), ('gakkaB', '午後')]

    print("=" * 80)
    print("全年度の解答上の注意")
    print("=" * 80)

    for year in years:
        print(f"\n### {year}年度")
        for part_code, part_name in parts:
            docx_path = os.path.join(base_dir, f'{year}{part_code}_mondai.docx')
            if not os.path.exists(docx_path):
                print(f"  {part_name}: DOCXファイルが見つかりません")
                continue

            rules = extract_exam_rules_from_docx(docx_path)

            if not rules:
                print(f"  {part_name}: 解答上の注意が抽出できませんでした")
                continue

            total_questions = max(r['no_to'] for r in rules) if rules else 0
            total_required = sum(r['required'] for r in rules)

            print(f"  {part_name}: {total_questions}問中{total_required}問解答")
            for rule in rules:
                mode_str = "全問解答" if rule['mode'] == 'ALL' else f"{rule['total']}問中{rule['required']}問選択"
                print(f"    {rule['range']}: {mode_str}")

    print("\n" + "=" * 80)

if __name__ == '__main__':
    main()
