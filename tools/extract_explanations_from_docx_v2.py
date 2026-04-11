#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
解説文集Wordファイルから選択肢説明文を抽出してCSVに変換（改善版v2）

改善内容:
- 令和7年度: 新形式パーサー（独立ID行、数字付き選択肢、【まとめ】セクション）
- 令和1-3年度: 旧形式パーサー（統合解説 "1.誤り。～ 2.適当。～"）
- 令和4-6年度: 中間形式パーサー（"選択肢1." 形式）の精度向上

Input:
  C:/Users/masam/Downloads/１級土木-20260214T233348Z-1-001/１級土木/*.docx

Output:
  C:/ProgramData/Generative AI/Github/doboku-14w-training/data/explanations_complete.csv

Usage:
  python extract_explanations_from_docx_v2.py
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
INPUT_DIR = Path("C:/Users/owner/KeyenceRK/１級土木施工管理技術検定愛一時検定_eラーニングサイト/１級土木")
OUTPUT_CSV = Path("C:/ProgramData/Generative AI/Github/doboku-14w-training/data/explanations_complete.csv")

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

    年度別の構成:
    - 令和元〜5年度: A 48問 + B 48問 = 96問
    - 令和6年度: A 35問のみ = 35問
    - 令和7年度: A 66問 + B 35問 = 101問
    """
    if year_str not in YEAR_ID_MAPPING:
        return None

    prefix, start_id, end_id = YEAR_ID_MAPPING[year_str]

    # ID範囲チェック
    if not (start_id <= internal_id <= end_id):
        return None

    # 問題番号計算（0始まり）
    question_num = internal_id - start_id

    # 年度別のA/B区分判定
    if year_str == "令和6年度":
        # 令和6年度は問題Aのみ（35問）
        section = "A"
        section_num = question_num + 1  # 001-035
    elif year_str == "令和7年度":
        # 令和7年度: A 66問（ID 86605-86670）+ B 35問（ID 86671-86705）
        if question_num < 66:
            section = "A"
            section_num = question_num + 1  # 001-066
        else:
            section = "B"
            section_num = question_num - 65  # 001-035
    else:
        # 令和元〜5年度: A 61問 + B 35問 = 96問
        if question_num < 61:
            section = "A"
            section_num = question_num + 1  # 001-061
        else:
            section = "B"
            section_num = question_num - 60  # 001-035

    return f"{prefix}{section}-{section_num:03d}"


# ========================================
# 令和7年度用: 新形式パーサー
# ========================================
def extract_new_format_r7(full_text):
    """
    令和7年度の新形式パーサー
    - 独立ID行: "ID: 86605"
    - 選択肢: "1.", "2.", "3.", "4."
    - 【まとめ】セクション

    Returns:
        dict: {"A": "...", "B": "...", "C": "...", "D": "...", "short": "...", "long": "..."}
    """
    explanations = {"A": "", "B": "", "C": "", "D": ""}
    explain_short = ""
    explain_long = ""

    # 数字付き選択肢の抽出（1. 〜 4.）
    for i in range(1, 5):
        choice_letter = chr(64 + i)  # 1->A, 2->B, 3->C, 4->D

        # パターン: "選択肢1." または単独 "1." から次の選択肢または【まとめ】まで
        pattern = rf'(?:選択肢)?{i}\.(.*?)(?=(?:選択肢)?{i+1}\.|【?まとめ|━━|────|$)'
        match = re.search(pattern, full_text, re.DOTALL)

        if match:
            text = match.group(1).strip()
            # "まとめ" という単独行があれば削除
            text = re.sub(r'^まとめ\s*$', '', text, flags=re.MULTILINE)
            explanations[choice_letter] = text

    # explainShort: 【解説】から最初の選択肢の前まで
    match_short = re.search(r'【解説】\s*(.*?)(?=(?:選択肢)?1\.)', full_text, re.DOTALL)
    if match_short:
        explain_short = match_short.group(1).strip()

    # explainLong: 【まとめ】セクション
    match_long = re.search(r'【まとめ】\s*(.*?)(?=━━|────|$)', full_text, re.DOTALL)
    if match_long:
        explain_long = match_long.group(1).strip()

    return {
        "A": explanations["A"],
        "B": explanations["B"],
        "C": explanations["C"],
        "D": explanations["D"],
        "short": explain_short,
        "long": explain_long,
    }


# ========================================
# 令和1-3年度用: 旧形式パーサー
# ========================================
def extract_old_format_r1_r3(full_text):
    """
    令和1-3年度の旧形式パーサー
    - パターンA: "選択肢1. ～ 選択肢2. ～" 形式（詳細解説あり）
    - パターンB: "1.誤り。～ 2.適当。～" 形式（統合解説）
    - 区切り線: "────────"

    Returns:
        dict: {"A": "...", "B": "...", "C": "...", "D": "...", "short": "...", "long": "..."}
    """
    explanations = {"A": "", "B": "", "C": "", "D": ""}
    explain_short = ""
    explain_long = ""

    # 【解説】から区切り線までを取得
    match_all = re.search(r'【解説】\s*(.*?)(?=────|━━|$)', full_text, re.DOTALL)
    if match_all:
        explanation_text = match_all.group(1).strip()

        # パターンA: "選択肢1." という明示的な形式があるか確認
        if re.search(r'選択肢1\.', explanation_text):
            # 詳細解説あり形式
            # explainShort: 最初の「選択肢1.」の前まで
            match_short = re.search(r'^(.*?)(?=選択肢1\.)', explanation_text, re.DOTALL)
            if match_short:
                explain_short = match_short.group(1).strip()

            # 各選択肢を抽出（選択肢1. 〜 選択肢4.）
            for i in range(1, 5):
                choice_letter = chr(64 + i)  # 1->A, 2->B, 3->C, 4->D
                pattern = rf'選択肢{i}\.(.*?)(?=選択肢{i+1}\.|$)'
                match = re.search(pattern, explanation_text, re.DOTALL)
                if match:
                    explanations[choice_letter] = match.group(1).strip()

        else:
            # パターンB: 統合解説形式（"1.誤り。～ 2.適当。～" または "1→誤り。～ 2→適当。～"）
            explain_short = explanation_text  # 統合解説全体をshortに

            # 各選択肢を抽出（1. 〜 4. または 1→ 〜 4→）
            for i in range(1, 5):
                choice_letter = chr(64 + i)  # 1->A, 2->B, 3->C, 4->D
                # パターン: "1.誤り。～" または "1→誤り。～" から次の選択肢の前まで（または末尾まで）
                # "1." または "1→" の両方に対応
                pattern = rf'{i}[\.\→](.*?)(?={i+1}[\.\→]|$)'
                match = re.search(pattern, explanation_text, re.DOTALL)
                if match:
                    explanations[choice_letter] = match.group(1).strip()

    return {
        "A": explanations["A"],
        "B": explanations["B"],
        "C": explanations["C"],
        "D": explanations["D"],
        "short": explain_short,
        "long": explain_long,
    }


# ========================================
# 令和4-6年度用: 中間形式パーサー（改善版）
# ========================================
def extract_middle_format_r4_r6(full_text):
    """
    令和4-6年度の中間形式パーサー（改善版）
    - 選択肢: "選択肢1." 形式
    - 各選択肢に詳細説明あり

    Returns:
        dict: {"A": "...", "B": "...", "C": "...", "D": "...", "short": "...", "long": "..."}
    """
    explanations = {"A": "", "B": "", "C": "", "D": ""}
    explain_short = ""
    explain_long = ""

    # 選択肢で分割（選択肢1. 〜 選択肢4.）
    for i in range(1, 5):
        choice_letter = chr(64 + i)  # 1->A, 2->B, 3->C, 4->D

        # パターン: "選択肢1." から "選択肢2." または区切り線までを抽出
        pattern = rf'選択肢{i}\.(.*?)(?=選択肢{i+1}\.|【?まとめ|URL:|━━|────|$)'
        match = re.search(pattern, full_text, re.DOTALL)

        if match:
            explanations[choice_letter] = match.group(1).strip()

    # explainShort: 【解説】から最初の「選択肢1.」の前まで
    match_short = re.search(r'【解説】\s*(.*?)(?=選択肢1\.)', full_text, re.DOTALL)
    if match_short:
        explain_short = match_short.group(1).strip()

    # explainLong: 【まとめ】セクション（存在する場合）
    match_long = re.search(r'【?まとめ】?\s*(.*?)(?=URL:|━━|────|$)', full_text, re.DOTALL)
    if match_long:
        explain_long = match_long.group(1).strip()

    return {
        "A": explanations["A"],
        "B": explanations["B"],
        "C": explanations["C"],
        "D": explanations["D"],
        "short": explain_short,
        "long": explain_long,
    }


# ========================================
# 年度別のパーサー選択
# ========================================
def extract_explanations_auto(full_text, year_str):
    """
    年度に応じて適切なパーサーを自動選択
    """
    if year_str == "令和7年度":
        return extract_new_format_r7(full_text)
    elif year_str in ["令和元年度", "令和2年度", "令和3年度"]:
        return extract_old_format_r1_r3(full_text)
    else:  # 令和4-6年度
        return extract_middle_format_r4_r6(full_text)


# ========================================
# Wordファイルから問題データを抽出
# ========================================
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
        # パターン2: "問1（ID: 47839）" (令和元〜6年度)
        match = re.search(r'ID:\s*(\d+)', text)
        if match:
            current_id = int(match.group(1))
            qid = generate_qid(year_str, current_id)

            if qid:
                # 【解説】セクションを探して、その全文を取得
                explanation_text = ""

                for j in range(i + 1, min(i + 150, len(para_list))):  # 次の150段落以内を探索（長い解説に対応）
                    section_text = para_list[j].text.strip()

                    if section_text.startswith("【解説】"):
                        # 【解説】から次の問題（━━ または ──── または ID:）までのテキストを連結
                        for k in range(j, min(j + 150, len(para_list))):
                            chunk = para_list[k].text.strip()

                            # 次の問題に到達したら終了
                            if (chunk.startswith("━━") or
                                chunk.startswith("────") or
                                (k > j and re.search(r'問\d+（ID:\s*\d+）', chunk)) or
                                (k > j and re.match(r'^ID:\s*\d+$', chunk))):
                                break

                            explanation_text += chunk + " "

                        # 年度に応じたパーサーで抽出
                        parsed = extract_explanations_auto(explanation_text, year_str)

                        # データを追加
                        results.append({
                            "qId": qid,
                            "explainA": parsed["A"],
                            "explainB": parsed["B"],
                            "explainC": parsed["C"],
                            "explainD": parsed["D"],
                            "explainShort": parsed["short"],
                            "explainLong": parsed["long"],
                        })

                        break

        i += 1

    return results


# ========================================
# メイン処理
# ========================================
def main():
    """メイン処理"""
    print("=== 解説文集からCSV抽出開始（改善版v2）===\n")

    # 出力ディレクトリ作成
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)

    # ベースファイルのみ処理（(1), (2)付きは除外）
    all_data = []
    year_stats = {}

    for year_str, (prefix, start_id, end_id) in YEAR_ID_MAPPING.items():
        docx_file = INPUT_DIR / f"1級土木 解説文集 {year_str}.docx"

        if not docx_file.exists():
            print(f"⚠ スキップ: {docx_file.name} (ファイルが存在しません)")
            continue

        print(f"処理中: {docx_file.name}")

        try:
            data = extract_from_docx(docx_file, year_str)
            all_data.extend(data)

            # 統計を計算
            total = len(data)
            complete = sum(1 for r in data if all([r['explainA'], r['explainB'], r['explainC'], r['explainD']]))
            year_stats[year_str] = (total, complete)

            print(f"  → {total} 問題を抽出 (選択肢説明完全: {complete}問 / {complete*100//total if total else 0}%)")
        except Exception as e:
            print(f"  ✗ エラー: {e}")

    # CSV出力
    print(f"\n=== CSV出力: {OUTPUT_CSV} ===")

    with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8-sig') as f:
        fieldnames = ["qId", "explainA", "explainB", "explainC", "explainD", "explainShort", "explainLong"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)

        writer.writeheader()
        writer.writerows(all_data)

    print(f"✓ 完了: {len(all_data)} 問題をCSVに出力しました\n")

    # 統計サマリー
    print("=== 年度別統計 ===")
    total_complete = 0
    total_all = 0
    for year_str, (total, complete) in year_stats.items():
        year_prefix = year_str[:3]  # "令和7" -> "R7"
        year_prefix = year_prefix.replace("令和", "R")
        print(f"{year_prefix}: {total}問 → 選択肢説明完全: {complete}問 ({complete*100//total if total else 0}%)")
        total_complete += complete
        total_all += total

    print(f"\n全体: {total_all}問 → 選択肢説明完全: {total_complete}問 ({total_complete*100//total_all if total_all else 0}%)")


if __name__ == "__main__":
    main()
