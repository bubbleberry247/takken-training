#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
R1〜R3年度の旧形式パーサー

形式の特徴:
    【解説】
    １→設問通りです。注入速度は...
    ２→設問通りです。注入圧力は...
    ３→誤りです。標準ステップ長は...
    ４→設問通りです。注入孔の間隔は...

対象: R1gakkaA-049〜061, R2gakkaA-049〜061, R3gakkaA-049〜061（39問）
"""

import sys
import io
import csv
import json
from pathlib import Path
from docx import Document
from datetime import datetime
import re

# UTF-8出力設定
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

ORIGINAL_FOLDER = Path(r"C:\Users\masam\Downloads\１級土木-20260214T233348Z-1-001\１級土木")
CSV_PATH = Path(r"C:\ProgramData\Generative AI\Github\doboku-14w-training\tools\questionbank_drive_import.csv")

FILES = {
    'R1': ("1級土木 解説文集 令和元年度.docx", list(range(49, 62))),
    'R2': ("1級土木 解説文集 令和2年度.docx", list(range(49, 62))),
    'R3': ("1級土木 解説文集 令和3年度(1).docx", list(range(49, 62))),
}


def extract_problem_explanations(doc, problem_num):
    """
    特定の問題番号の解説を抽出

    Returns:
        dict: {explainA, explainB, explainC, explainD, explainShort}
    """
    # 問題セクションを抽出
    in_problem = False
    problem_paras = []

    for para in doc.paragraphs:
        text = para.text.strip()

        # 問題開始
        if f'問{problem_num}' in text and ('ID:' in text or '（ID:' in text):
            in_problem = True
            problem_paras.append(text)
            continue

        if in_problem:
            problem_paras.append(text)
            # 次の問題または区切り線で終了
            if f'問{problem_num + 1}' in text or '────' in text:
                break

    if not problem_paras:
        return None

    # 解説セクションを抽出
    explanation_text = ""
    in_explanation = False

    for text in problem_paras:
        if '【解説】' in text:
            in_explanation = True
            explanation_text = text.replace('【解説】', '').strip()
            continue

        if in_explanation:
            if '────' in text:
                break
            explanation_text += " " + text

    if not explanation_text:
        return None

    # 解説をパース
    return parse_old_format_explanation(explanation_text)


def parse_old_format_explanation(text):
    """
    旧形式の解説をパース

    形式: １→判定。内容...  ２→判定。内容...
    """
    # パターン: 全角数字 + → + テキスト
    pattern = r'([１２３４])→(.+?)(?=[１２３４]→|$)'
    matches = re.findall(pattern, text, re.DOTALL)

    if not matches:
        # フォールバック: 英数字1-4
        pattern2 = r'([1234])[。．\s](.+?)(?=[1234][。．]|$)'
        matches = re.findall(pattern2, text, re.DOTALL)

    explains = {}

    for num_str, content in matches:
        # 全角数字を半角に変換
        num_map = {'１': 1, '２': 2, '３': 3, '４': 4, '1': 1, '2': 2, '3': 3, '4': 4}
        num = num_map.get(num_str, 0)

        if num == 0:
            continue

        # 内容を整理
        cleaned = ' '.join(content.split())

        # 選択肢に割り当て
        if num == 1:
            explains['explainA'] = cleaned
        elif num == 2:
            explains['explainB'] = cleaned
        elif num == 3:
            explains['explainC'] = cleaned
        elif num == 4:
            explains['explainD'] = cleaned

    # explainShortを生成
    first_explain = explains.get('explainA', '') or explains.get('explainB', '') or text[:200]
    explains['explainShort'] = first_explain[:200]

    # 不足している選択肢を空文字で埋める
    for key in ['explainA', 'explainB', 'explainC', 'explainD']:
        if key not in explains:
            explains[key] = ''

    return explains


def extract_all_problems(year, filename, target_nums):
    """
    指定年度の全対象問題を抽出
    """
    file_path = ORIGINAL_FOLDER / filename
    if not file_path.exists():
        print(f"❌ ファイルが見つかりません: {filename}")
        return {}

    doc = Document(file_path)
    results = {}

    for num in target_nums:
        qid = f"{year}gakkaA-{num:03d}"
        explanations = extract_problem_explanations(doc, num)

        if explanations:
            results[qid] = explanations
            print(f"✓ {qid}: 抽出成功")
        else:
            print(f"⚠️  {qid}: 抽出失敗")

    return results


def merge_to_csv(all_explanations, csv_path):
    """CSVに統合"""
    # バックアップ作成
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = csv_path.parent / f"{csv_path.stem}_backup_{timestamp}{csv_path.suffix}"

    import shutil
    shutil.copy2(csv_path, backup_path)
    print(f"\n✓ バックアップ作成: {backup_path.name}")

    # CSV読み込み
    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    # 統計
    stats = {'total': len(rows), 'updated': 0, 'skipped': 0}

    # 更新
    for row in rows:
        qid = row.get('qId', '')

        if qid in all_explanations:
            exp = all_explanations[qid]

            row['explainA'] = exp['explainA']
            row['explainB'] = exp['explainB']
            row['explainC'] = exp['explainC']
            row['explainD'] = exp['explainD']

            if not row.get('explainShort', '').strip():
                row['explainShort'] = exp['explainShort']

            stats['updated'] += 1
        else:
            stats['skipped'] += 1

    # CSV書き戻し
    with open(csv_path, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"✓ CSV更新完了: {csv_path.name}")

    return stats


def main():
    print("=== R1〜R3年度 旧形式パーサー ===\n")

    all_explanations = {}

    for year, (filename, target_nums) in FILES.items():
        print(f"[{year}年度] {filename}")
        results = extract_all_problems(year, filename, target_nums)
        all_explanations.update(results)
        print(f"  → {len(results)}問抽出\n")

    print(f"総抽出数: {len(all_explanations)}問\n")

    # CSV統合
    print("[CSV統合]")
    stats = merge_to_csv(all_explanations, CSV_PATH)

    # 結果レポート
    print("\n" + "="*80)
    print("抽出結果レポート")
    print("="*80)
    print(f"CSV総問題数:     {stats['total']}問")
    print(f"更新された問題:   {stats['updated']}問 ✅")
    print(f"スキップ:        {stats['skipped']}問")
    print("="*80)

    if stats['updated'] > 0:
        print("\n✅ R1〜R3年度の旧形式解説文抽出完了！")
        print(f"   次: R4〜R5年度の中間形式抽出")

    return all_explanations


if __name__ == '__main__':
    main()
