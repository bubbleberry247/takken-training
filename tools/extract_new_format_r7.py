#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
R7年度の新形式パーサー

形式の特徴:
    【解説】
    統合解説（選択肢別説明なし）

対象: R7gakkaA-005（1問のみ）
"""

import sys
import io
import csv
from pathlib import Path
from docx import Document
from datetime import datetime
import re

# UTF-8出力設定
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

ORIGINAL_FOLDER = Path(r"C:\Users\masam\Downloads\１級土木-20260214T233348Z-1-001\１級土木")
CSV_PATH = Path(r"C:\ProgramData\Generative AI\Github\doboku-14w-training\tools\questionbank_drive_import.csv")

R7_FILE = "1級土木 解説文集 令和7年度.docx"
TARGET_PROBLEM = 5


def extract_r7_problem_5():
    """
    R7年度問5の統合解説を抽出

    Returns:
        dict: {explainShort}
    """
    file_path = ORIGINAL_FOLDER / R7_FILE
    if not file_path.exists():
        print(f"❌ ファイルが見つかりません: {R7_FILE}")
        return None

    doc = Document(file_path)

    # 問5を探す
    in_problem = False
    in_explanation = False
    explanation_lines = []

    for para in doc.paragraphs:
        text = para.text.strip()

        # 問5開始（「令和7年度 問5」パターン）
        if f'令和7年度 問{TARGET_PROBLEM}' in text:
            in_problem = True
            continue

        if in_problem:
            # 解説セクション開始
            if '【解説】' in text:
                in_explanation = True
                # 【解説】の後のテキストも含める
                explanation_text = text.replace('【解説】', '').strip()
                if explanation_text:
                    explanation_lines.append(explanation_text)
                continue

            # 次の問題または区切り線で終了
            if f'問{TARGET_PROBLEM + 1}' in text or '━━━━' in text or 'ID:' in text:
                break

            # 解説本文を収集
            if in_explanation and text:
                # URL行は除外
                if not text.startswith('URL:'):
                    explanation_lines.append(text)

    if not explanation_lines:
        return None

    # 統合解説を作成
    full_explanation = ' '.join(explanation_lines)

    return {
        'explainShort': full_explanation[:500],  # 最初の500文字
        'explainLong': full_explanation,  # 全文（オプション）
    }


def merge_to_csv(explanation, csv_path):
    """CSVに統合"""
    # バックアップ作成
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = csv_path.parent / f"{csv_path.stem}_backup_{timestamp}{csv_path.suffix}"

    import shutil
    shutil.copy2(csv_path, backup_path)
    print(f"✓ バックアップ作成: {backup_path.name}")

    # CSV読み込み
    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    # 統計
    stats = {'total': len(rows), 'updated': 0, 'skipped': 0}

    # R7gakkaA-005を更新
    qid = f"R7gakkaA-{TARGET_PROBLEM:03d}"
    for row in rows:
        if row.get('qId', '') == qid:
            # explainShortのみ更新（explainA-Dは空のまま）
            row['explainShort'] = explanation['explainShort']
            stats['updated'] = 1
            print(f"✓ {qid}: 統合解説を更新")
            break
    else:
        print(f"⚠️  {qid}: CSVに存在しません")
        stats['skipped'] = 1

    # CSV書き戻し
    with open(csv_path, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"✓ CSV更新完了: {csv_path.name}")

    return stats


def main():
    print("=== R7年度 新形式パーサー ===\n")

    print(f"[R7年度] {R7_FILE}")
    print(f"対象: 問{TARGET_PROBLEM}のみ\n")

    # 解説抽出
    explanation = extract_r7_problem_5()

    if not explanation:
        print(f"❌ 問{TARGET_PROBLEM}の解説が抽出できませんでした")
        return None

    print(f"✓ 問{TARGET_PROBLEM}の統合解説を抽出")
    print(f"  文字数: {len(explanation['explainLong'])}文字")
    print(f"  プレビュー: {explanation['explainShort'][:100]}...\n")

    # CSV統合
    print("[CSV統合]")
    stats = merge_to_csv(explanation, CSV_PATH)

    # 結果レポート
    print("\n" + "="*80)
    print("抽出結果レポート")
    print("="*80)
    print(f"CSV総問題数:     {stats['total']}問")
    print(f"更新された問題:   {stats['updated']}問 ✅")
    print(f"スキップ:        {stats['skipped']}問")
    print("="*80)

    if stats['updated'] > 0:
        print("\n✅ R7年度新形式解説文抽出完了！")
        print(f"   合計抽出: R1-R3(39問) + R4-R5(25問) + R7(1問) = 65問")

    return explanation


if __name__ == '__main__':
    main()
