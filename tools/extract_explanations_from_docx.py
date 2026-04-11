#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
解説文集Wordファイルから選択肢説明文を抽出してCSVに変換

Input:
  C:/Users/masam/Downloads/１級土木-20260214T233348Z-1-001/１級土木/*.docx
  - 1級土木 解説文集 令和元年度.docx
  - 1級土木 解説文集 令和2年度.docx
  - ...
  - 1級土木 解説文集 令和7年度.docx

Output:
  C:/ProgramData/Generative AI/Github/doboku-14w-training/data/explanations.csv
  - qId: R1gakkaA-001, R2gakkaB-015, etc.
  - explainA, explainB, explainC, explainD: 各選択肢の説明文
  - explainShort: 問題全体の短い解説
  - explainLong: 問題のまとめ

Usage:
  python extract_explanations_from_docx.py

Notes:
  - 重複ファイル（(1), (2)付き）は自動的にスキップ
  - 年度によって選択肢説明の有無が異なる（新しい年度ほど詳細）
  - 令和4年度以降: ほぼ全問に選択肢説明あり（96-100%）
  - 令和元〜3年度: 一部の問題のみ選択肢説明あり（11-19%）
"""

import sys
import io
import re
import csv
from pathlib import Path
from docx import Document

# UTF-8出力設定
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# パス設定
INPUT_DIR = Path("C:/Users/masam/Downloads/１級土木-20260214T233348Z-1-001/１級土木")
OUTPUT_CSV = Path("C:/ProgramData/Generative AI/Github/doboku-14w-training/data/explanations.csv")

# 年度とID範囲のマッピング（qIdパターン生成用）
YEAR_ID_MAPPING = {
    "令和元年度": ("R1gakka", 47839, 47934),
    "令和2年度": ("R2gakka", 53625, 53720),
    "令和3年度": ("R3gakka", 58753, 58848),
    "令和4年度": ("R4gakka", 67671, 67766),
    "令和5年度": ("R5gakka", 74717, 74812),
    "令和6年度": ("R6gakka", 78561, 78595),
    "令和7年度": ("R7gakka", 86605, 86705),
}

# qId生成関数
def generate_qid(year_str, internal_id):
    """
    年度文字列とinternal IDからqIdを生成
    例: 令和7年度 + 86605 → R7gakkaA-001
    """
    if year_str not in YEAR_ID_MAPPING:
        return None

    prefix, start_id, end_id = YEAR_ID_MAPPING[year_str]

    # ID範囲チェック
    if not (start_id <= internal_id <= end_id):
        return None

    # 問題番号計算（0始まり）
    question_num = internal_id - start_id

    # A/B区分判定（0-47: A, 48-95: B）
    if question_num < 48:
        section = "A"
        section_num = question_num + 1  # 001-048
    else:
        section = "B"
        section_num = question_num - 47  # 001-048

    return f"{prefix}{section}-{section_num:03d}"


def extract_choice_explanations(full_text):
    """
    【解説】セクションの全文から選択肢の説明文を抽出

    Args:
        full_text: 【解説】セクション全体のテキスト

    Returns:
        dict: {"A": "選択肢1の説明", "B": "選択肢2の説明", ...}
    """
    explanations = {"A": "", "B": "", "C": "", "D": ""}

    # 選択肢で分割（選択肢1. 〜 選択肢4.）
    # 各選択肢のテキストを抽出
    for i in range(1, 5):
        choice_letter = chr(64 + i)  # 1->A, 2->B, 3->C, 4->D

        # 選択肢i. から 選択肢(i+1). の直前まで、または まとめ/URL/区切り線までを抽出
        pattern = rf'選択肢{i}\.(.*?)(?=選択肢{i+1}\.|【?まとめ|URL:|━━|$)'
        match = re.search(pattern, full_text, re.DOTALL)

        if match:
            explanations[choice_letter] = match.group(1).strip()

    return explanations


def extract_short_long_explanation(full_text):
    """
    【解説】セクションの全体解説と【まとめ】を抽出

    Args:
        full_text: 【解説】セクション全体のテキスト

    Returns:
        tuple: (explainShort, explainLong)
    """
    explain_short = ""
    explain_long = ""

    # explainShort: 【解説】から最初の「選択肢1.」の前まで
    match_short = re.search(r'^(.*?)(?=選択肢1\.)', full_text, re.DOTALL)
    if match_short:
        explain_short = match_short.group(1).strip()

    # explainLong: 【まとめ】セクション（存在する場合）
    match_long = re.search(r'【?まとめ】?\s*(.*?)(?=URL:|━━|$)', full_text, re.DOTALL)
    if match_long:
        explain_long = match_long.group(1).strip()

    return explain_short, explain_long


def extract_from_docx(docx_path, year_str):
    """
    Wordファイルから問題データを抽出

    Args:
        docx_path: Wordファイルのパス
        year_str: 年度文字列（例: "令和7年度"）

    Returns:
        list: [{qId, explainA, explainB, explainC, explainD, explainShort, explainLong}, ...]
    """
    doc = Document(docx_path)
    para_list = doc.paragraphs

    results = []
    current_id = None

    i = 0
    while i < len(para_list):
        text = para_list[i].text.strip()

        # ID行を検出（2つのパターンに対応）
        # パターン1: "ID: 86605" (令和7年度)
        # パターン2: "問1（ID: 53625）" (令和元〜6年度)
        match = re.search(r'ID:\s*(\d+)', text)
        if match:
            current_id = int(match.group(1))
            qid = generate_qid(year_str, current_id)

            if qid:
                # 【解説】セクションを探して、その全文を取得
                explanation_text = ""

                for j in range(i + 1, min(i + 100, len(para_list))):  # 次の100段落以内を探索
                    section_text = para_list[j].text.strip()

                    if section_text.startswith("【解説】"):
                        # 【解説】から次の問題（━━ または ID:）までのテキストを連結
                        for k in range(j, min(j + 100, len(para_list))):
                            chunk = para_list[k].text.strip()

                            # 次の問題に到達したら終了
                            if (chunk.startswith("━━") or
                                (k > j and re.search(r'ID:\s*\d+', chunk))):
                                break

                            explanation_text += chunk + " "

                        # 抽出処理
                        choice_explanations = extract_choice_explanations(explanation_text)
                        explain_short, explain_long = extract_short_long_explanation(explanation_text)

                        # データを追加
                        results.append({
                            "qId": qid,
                            "explainA": choice_explanations["A"],
                            "explainB": choice_explanations["B"],
                            "explainC": choice_explanations["C"],
                            "explainD": choice_explanations["D"],
                            "explainShort": explain_short,
                            "explainLong": explain_long,
                        })

                        break

        i += 1

    return results


def main():
    """メイン処理"""
    print("=== 解説文集からCSV抽出開始 ===\n")

    # 出力ディレクトリ作成
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)

    # ベースファイルのみ処理（(1), (2)付きは除外）
    all_data = []

    for year_str, (prefix, start_id, end_id) in YEAR_ID_MAPPING.items():
        docx_file = INPUT_DIR / f"1級土木 解説文集 {year_str}.docx"

        if not docx_file.exists():
            print(f"⚠ スキップ: {docx_file.name} (ファイルが存在しません)")
            continue

        print(f"処理中: {docx_file.name}")

        try:
            data = extract_from_docx(docx_file, year_str)
            all_data.extend(data)
            print(f"  → {len(data)} 問題を抽出")
        except Exception as e:
            print(f"  ✗ エラー: {e}")

    # CSV出力
    print(f"\n=== CSV出力: {OUTPUT_CSV} ===")

    with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8-sig') as f:
        fieldnames = ["qId", "explainA", "explainB", "explainC", "explainD", "explainShort", "explainLong"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)

        writer.writeheader()
        writer.writerows(all_data)

    print(f"✓ 完了: {len(all_data)} 問題をCSVに出力しました")


if __name__ == "__main__":
    main()
