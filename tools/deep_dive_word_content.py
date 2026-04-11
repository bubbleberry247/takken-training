#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Word原本ファイルの深掘り調査
- 令和7年度（最大サイズ169KB）の内容詳細
- 抽出率0%年度の原因特定
- 選択肢説明とまとめの存在確認
"""

import sys
import io
from pathlib import Path
from docx import Document
import re

# UTF-8出力設定
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

ORIGINAL_FOLDER = Path(r"C:\Users\masam\Downloads\１級土木-20260214T233348Z-1-001\１級土木")

def analyze_word_structure(file_path):
    """Word文書の構造を詳細分析"""
    try:
        doc = Document(file_path)

        paragraphs = []
        for p in doc.paragraphs:
            text = p.text.strip()
            if text:
                paragraphs.append(text)

        # パターン検出
        patterns = {
            '問題番号': re.compile(r'問題?\s*(\d+)'),
            '選択肢': re.compile(r'^[1234①②③④]\s*[．.]'),
            '解説開始': re.compile(r'【?解説】?'),
            '誤り': re.compile(r'誤り|適当でない|不適当'),
            '設問の通り': re.compile(r'設問の通り'),
            '区切り線': re.compile(r'─{10,}')
        }

        structure = {
            'total_paragraphs': len(paragraphs),
            'detected_patterns': {},
            'sample_problems': [],
            'has_explanations': False,
            'has_choices': False,
            'explanation_count': 0,
            'choice_explanation_count': 0
        }

        # パターンカウント
        for pattern_name, pattern_re in patterns.items():
            count = sum(1 for p in paragraphs if pattern_re.search(p))
            structure['detected_patterns'][pattern_name] = count

        # 解説・選択肢説明の検出
        structure['has_explanations'] = structure['detected_patterns']['解説開始'] > 0
        structure['explanation_count'] = structure['detected_patterns']['解説開始']

        # 選択肢説明のカウント
        in_choice_section = False
        for para in paragraphs:
            if patterns['選択肢'].search(para):
                in_choice_section = True
            if in_choice_section and (patterns['設問の通り'].search(para) or
                                     patterns['誤り'].search(para)):
                structure['choice_explanation_count'] += 1

        structure['has_choices'] = structure['choice_explanation_count'] > 0

        # サンプル問題抽出（最初の2問）
        current_problem = None
        problem_content = []
        problem_count = 0

        for para in paragraphs:
            match = patterns['問題番号'].search(para)
            if match:
                if current_problem and problem_content:
                    structure['sample_problems'].append({
                        'number': current_problem,
                        'content': problem_content[:10]  # 最初の10段落
                    })
                    problem_count += 1
                    if problem_count >= 2:
                        break

                current_problem = match.group(1)
                problem_content = [para]
            elif current_problem:
                problem_content.append(para)

        return structure

    except Exception as e:
        return {
            'error': str(e),
            'success': False
        }

def main():
    print("=" * 80)
    print("Word原本ファイル深掘り調査")
    print("=" * 80)

    # 調査対象ファイル
    target_files = [
        ("令和7年度 (最大サイズ)", "1級土木 解説文集 令和7年度.docx"),
        ("令和1年度 (抽出率0%)", "1級土木 解説文集 令和元年度.docx"),
        ("令和2年度 (抽出率2.1%)", "1級土木 解説文集 令和2年度.docx"),
        ("令和3年度 (抽出率0%)", "1級土木 解説文集 令和3年度(1).docx"),
        ("令和4年度 (抽出率2-4%)", "1級土木 解説文集 令和4年度.docx"),
        ("令和5年度 (抽出率44-92%)", "1級土木 解説文集 令和5年度.docx"),
        ("令和6年度 (抽出率77%)", "1級土木 解説文集 令和6年度.docx"),
    ]

    for label, filename in target_files:
        file_path = ORIGINAL_FOLDER / filename

        if not file_path.exists():
            print(f"\n## {label}")
            print(f"❌ ファイルが存在しません: {filename}")
            continue

        print(f"\n## {label}")
        print(f"ファイル: {filename}")
        print(f"サイズ: {file_path.stat().st_size / 1024:.1f} KB")

        structure = analyze_word_structure(file_path)

        if 'error' in structure:
            print(f"❌ エラー: {structure['error']}")
            continue

        print(f"\n### 構造分析")
        print(f"- 総段落数: {structure['total_paragraphs']}")
        print(f"- 解説あり: {'✓' if structure['has_explanations'] else '✗'} ({structure['explanation_count']} 箇所)")
        print(f"- 選択肢説明あり: {'✓' if structure['has_choices'] else '✗'} ({structure['choice_explanation_count']} 箇所)")

        print(f"\n### パターン検出")
        for pattern_name, count in structure['detected_patterns'].items():
            print(f"- {pattern_name}: {count}")

        if structure['sample_problems']:
            print(f"\n### サンプル（最初の問題）")
            problem = structure['sample_problems'][0]
            print(f"**問題 {problem['number']}**")
            for i, line in enumerate(problem['content'][:5], 1):
                preview = line[:80] + "..." if len(line) > 80 else line
                print(f"{i}. {preview}")

        print("\n" + "-" * 80)

    print("\n" + "=" * 80)
    print("調査完了")
    print("=" * 80)

    # 結論
    print("\n## 調査結論")
    print("\n### 説明文が不足している理由")
    print("1. **原本ファイルに説明文が存在しない可能性**")
    print("   - R1~R3年度: 段落数が少ない → 説明文が簡略版の可能性")
    print("   - R4年度: 選択肢説明はあるが「まとめ」が少ない")
    print("")
    print("2. **抽出スクリプトのパターンマッチング不足**")
    print("   - R5年度は抽出率44-92% → スクリプトは動作している")
    print("   - R1~R3年度は0-2% → 原本の形式が異なる可能性")
    print("")
    print("3. **令和7年度（169KB）は最大サイズ**")
    print("   - 最新年度で説明文が充実している可能性大")
    print("   - 抽出率27.1%/15.1% → 追加抽出の余地あり")
    print("")
    print("### 推奨アクション")
    print("1. 令和7年度の全コンテンツ再抽出（169KB → 最大の説明文源泉）")
    print("2. 令和1~3年度の原本確認（説明文が本当に存在するか）")
    print("3. 抽出スクリプトのパターン調整（年度別の形式差異に対応）")

if __name__ == '__main__':
    main()
