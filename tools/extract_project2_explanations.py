# coding: utf-8
"""
プロジェクト2のdocx解説文を正しい形式で抽出し、プロジェクト1のqIdに対応付ける
"""
import sys
import re
from pathlib import Path
from docx import Document
import csv
import json

sys.stdout.reconfigure(encoding='utf-8')

def determine_gakka_type(year, question_count):
    """
    年度と問題数から学科A/Bを判定
    - R1-R5: 学科A 61問、学科B 35問
    - R6-R7: 学科A 66問、学科B 35問
    """
    if year in ['R1', 'R2', 'R3', 'R4', 'R5']:
        if question_count >= 60:
            return 'both'  # AとB両方含まれている
        elif question_count >= 55:
            return 'A'  # 学科Aのみ
        else:
            return 'B'  # 学科Bのみ
    else:  # R6, R7
        if question_count >= 90:
            return 'both'
        elif question_count >= 60:
            return 'A'
        else:
            return 'B'

def extract_explanations_from_docx(docx_path):
    """docxファイルから問題番号と解説文を抽出"""
    try:
        doc = Document(docx_path)
        questions = {}
        current_q_num = None
        current_content = []

        for para in doc.paragraphs:
            text = para.text.strip()

            # 問題番号を検出
            patterns = [
                r'^No\.?\s*(\d+)',
                r'^問\s*(\d+)',
                r'^第?\s*(\d+)\s*問',
                r'^(\d+)[\.\)]\s+',
            ]

            matched = False
            for pattern in patterns:
                m = re.match(pattern, text, re.IGNORECASE)
                if m:
                    # 前の問題の解説を保存
                    if current_q_num is not None and current_content:
                        questions[current_q_num] = '\n'.join(current_content)

                    # 新しい問題番号
                    current_q_num = int(m.group(1))
                    current_content = [text]  # 問題番号の行も含める
                    matched = True
                    break

            if not matched and current_q_num is not None:
                # 問題番号以降の内容を蓄積
                if text:
                    current_content.append(text)

        # 最後の問題の解説を保存
        if current_q_num is not None and current_content:
            questions[current_q_num] = '\n'.join(current_content)

        return questions

    except Exception as e:
        print(f"  エラー: {e}")
        return {}

def map_to_qid(year, gakka_type, question_num):
    """問題番号をqIdに変換"""
    if gakka_type == 'both':
        # 学科A/Bが混在している場合
        if year in ['R1', 'R2', 'R3', 'R4', 'R5']:
            # 問1-61: 学科A, 問62-96: 学科B（問1-35に相当）
            if question_num <= 61:
                return f"{year}gakkaA-{question_num:03d}"
            else:
                return f"{year}gakkaB-{question_num-61:03d}"
        else:  # R6, R7
            # 問1-66: 学科A, 問67-101: 学科B（問1-35に相当）
            if question_num <= 66:
                return f"{year}gakkaA-{question_num:03d}"
            else:
                return f"{year}gakkaB-{question_num-66:03d}"
    elif gakka_type == 'A':
        return f"{year}gakkaA-{question_num:03d}"
    else:  # 'B'
        return f"{year}gakkaB-{question_num:03d}"

def main():
    base_dir = Path(r"C:\Users\masam\Desktop\KeyenceRK\１級土木施工管理技術検定愛一時検定_eラーニングサイト\１級土木")

    docx_files = [f for f in sorted(base_dir.glob("*.docx"))
                  if "(1)" not in f.name and "(2)" not in f.name]

    all_explanations = {}
    metadata = {}

    print("="*80)
    print("プロジェクト2のdocx解説文抽出")
    print("="*80)

    for docx_file in docx_files:
        # ファイル名から年度を抽出
        match = re.search(r'令和(\d+|元)年度', docx_file.name)
        if not match:
            continue

        year_str = match.group(1)
        if year_str == "元":
            year = "R1"
        else:
            year = f"R{year_str}"

        print(f"\n📄 {docx_file.name}")

        # 解説を抽出
        questions = extract_explanations_from_docx(docx_file)

        if not questions:
            print(f"  ⚠️ 解説が抽出できませんでした")
            continue

        # 学科A/Bを判定
        question_count = len(questions)
        gakka_type = determine_gakka_type(year, question_count)

        print(f"  問題数: {question_count}問")
        print(f"  学科判定: {gakka_type}")

        # qIdに変換
        for q_num, explanation in questions.items():
            qid = map_to_qid(year, gakka_type, q_num)
            all_explanations[qid] = {
                'qId': qid,
                'year': year,
                'gakka': gakka_type,
                'original_number': q_num,
                'explanation': explanation
            }
            print(f"    問{q_num:3d} → {qid}")

        metadata[year] = {
            'question_count': question_count,
            'gakka_type': gakka_type,
            'filename': docx_file.name
        }

    # 結果を保存
    output_file = Path(r"C:\ProgramData\Generative AI\Github\doboku-14w-training\tools\project2_explanations.json")

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'explanations': all_explanations,
            'metadata': metadata
        }, f, ensure_ascii=False, indent=2)

    print(f"\n\n" + "="*80)
    print("【抽出結果】")
    print("="*80)
    print(f"総解説数: {len(all_explanations)}問")
    print(f"保存先: {output_file}")

    # 年度別サマリー
    print(f"\n年度別:")
    for year in sorted(metadata.keys()):
        meta = metadata[year]
        print(f"  {year}: {meta['question_count']}問 (学科{meta['gakka_type']})")

if __name__ == "__main__":
    main()
