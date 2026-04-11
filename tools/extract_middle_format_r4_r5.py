#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
R4〜R5年度の中間形式パーサー

形式の特徴:
    【解説】
    選択肢1. ... 適当です。...
    選択肢2. ... 不適当です。...
    選択肢3. ... 適当です。...
    選択肢4. ... 適当です。...

対象: R4gakkaA-049〜061, R5gakkaA-049〜061（26問）
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
    'R4': ("1級土木 解説文集 令和4年度.docx", list(range(49, 62))),
    'R5': ("1級土木 解説文集 令和5年度(1).docx", list(range(49, 62))),
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
    return parse_middle_format_explanation(explanation_text)


def parse_middle_format_explanation(text):
    """
    中間形式の解説をパース

    形式: 選択肢1. ... 選択肢2. ...
    """
    # パターン: 選択肢 + 数字 + . + テキスト
    pattern = r'選択肢(\d+)\.\s*(.+?)(?=選択肢\d+\.|$)'
    matches = re.findall(pattern, text, re.DOTALL)

    if not matches:
        # フォールバック: パターンがない場合
        return {
            'explainA': '',
            'explainB': '',
            'explainC': '',
            'explainD': '',
            'explainShort': text[:500],
        }

    explains = {}

    for num_str, content in matches:
        num = int(num_str)

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
    print("=== R4〜R5年度 中間形式パーサー ===\n")

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
        print("\n✅ R4〜R5年度の中間形式解説文抽出完了！")
        print(f"   次: R7年度の新形式抽出")

    return all_explanations


if __name__ == '__main__':
    main()
