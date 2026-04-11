#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
R6年度（学科B）の解説文を抽出してCSVに統合

特徴:
    - ファイル内の問1〜35 → R6gakkaB-001〜035
    - ID 78561-78595から逆算
    - 【解説】セクションから選択肢別説明を抽出
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

# ファイルパス
R6_FILE = Path(r"C:\Users\masam\Downloads\１級土木-20260214T233348Z-1-001\１級土木\1級土木 解説文集 令和6年度.docx")
MAPPING_FILE = Path(__file__).parent / "r6_mapping.json"
CSV_PATH = Path(r"C:\ProgramData\Generative AI\Github\doboku-14w-training\tools\questionbank_drive_import.csv")


def load_mapping():
    """マッピングファイルを読み込み"""
    with open(MAPPING_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def extract_explanations():
    """
    R6年度の解説文を抽出

    Returns:
        dict: {qId: {explainA, explainB, explainC, explainD, explainShort}}
    """
    doc = Document(R6_FILE)
    mapping = load_mapping()

    # ID → qId の辞書
    id_to_qid = {m['id']: m['qid'] for m in mapping}

    explanations = {}
    current_id = None
    current_qid = None
    current_explanation = []
    in_explanation = False

    for para in doc.paragraphs:
        text = para.text.strip()
        if not text:
            continue

        # 問題開始（ID検出）
        match_id = re.search(r'問\d+[\s（]*ID[：:\s]*(\d+)', text)
        if match_id:
            # 前の問題の解説を処理
            if current_qid and current_explanation:
                result = parse_explanation('\n'.join(current_explanation), current_qid)
                if result:
                    explanations[current_qid] = result

            # 新しい問題
            current_id = int(match_id.group(1))
            current_qid = id_to_qid.get(current_id)
            current_explanation = []
            in_explanation = False
            continue

        # 解説セクション開始
        if '【解説】' in text:
            in_explanation = True
            # 【解説】の後のテキストも含める
            explanation_text = text.replace('【解説】', '').strip()
            if explanation_text:
                current_explanation.append(explanation_text)
            continue

        # 区切り線（次の問題）
        if '────' in text:
            # 現在の問題の解説を処理
            if current_qid and current_explanation:
                result = parse_explanation('\n'.join(current_explanation), current_qid)
                if result:
                    explanations[current_qid] = result

            current_id = None
            current_qid = None
            current_explanation = []
            in_explanation = False
            continue

        # 解説本文を収集
        if in_explanation:
            current_explanation.append(text)

    # 最後の問題を処理
    if current_qid and current_explanation:
        result = parse_explanation('\n'.join(current_explanation), current_qid)
        if result:
            explanations[current_qid] = result

    return explanations


def parse_explanation(text, qid):
    """
    解説テキストから選択肢別説明を抽出

    形式:
        選択肢1. ... 不正答となります。...
        選択肢2. ... 正答となります。...
    """
    # 選択肢パターン
    pattern = r'選択肢(\d+)\.\s*(.+?)(?=選択肢\d+\.|$)'
    matches = re.findall(pattern, text, re.DOTALL)

    if not matches:
        # フォールバック: 選択肢パターンがない場合
        return {
            'explainA': '',
            'explainB': '',
            'explainC': '',
            'explainD': '',
            'explainShort': text[:500],  # 最初の500文字を使用
        }

    # 選択肢別に整理
    explains = {}
    for num_str, content in matches:
        num = int(num_str)
        # 改行やスペースを整理
        cleaned = ' '.join(content.split())
        if num == 1:
            explains['explainA'] = cleaned
        elif num == 2:
            explains['explainB'] = cleaned
        elif num == 3:
            explains['explainC'] = cleaned
        elif num == 4:
            explains['explainD'] = cleaned

    # explainShortを生成（最初の選択肢の冒頭）
    first_explain = explains.get('explainA', '') or explains.get('explainB', '') or text[:200]
    explains['explainShort'] = first_explain[:200]

    # 不足している選択肢を空文字で埋める
    for key in ['explainA', 'explainB', 'explainC', 'explainD']:
        if key not in explains:
            explains[key] = ''

    return explains


def merge_to_csv(explanations, csv_path):
    """
    CSVに統合
    """
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
    stats = {
        'total': len(rows),
        'updated': 0,
        'skipped': 0,
    }

    # explainA-Dを更新
    for row in rows:
        qid = row.get('qId', '')

        if qid in explanations:
            exp = explanations[qid]

            # 更新
            row['explainA'] = exp['explainA']
            row['explainB'] = exp['explainB']
            row['explainC'] = exp['explainC']
            row['explainD'] = exp['explainD']

            # explainShortも更新（既存のものがない場合）
            if not row.get('explainShort', '').strip():
                row['explainShort'] = exp['explainShort']

            stats['updated'] += 1
            print(f"✓ {qid}: 更新完了")
        else:
            stats['skipped'] += 1

    # CSV書き戻し
    with open(csv_path, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\n✓ CSV更新完了: {csv_path.name}")

    return stats


def main():
    print("=== R6年度（学科B）解説文抽出 ===\n")

    # 1. マッピング確認
    print("[1/3] マッピング読み込み")
    mapping = load_mapping()
    print(f"✓ {len(mapping)}問のマッピング確認\n")

    # 2. 解説文抽出
    print("[2/3] 解説文抽出")
    explanations = extract_explanations()
    print(f"✓ {len(explanations)}問の解説文を抽出\n")

    # サンプル表示
    if explanations:
        sample_qid = list(explanations.keys())[0]
        sample = explanations[sample_qid]
        print(f"サンプル（{sample_qid}）:")
        print(f"  explainA: {sample['explainA'][:80]}...")
        print(f"  explainB: {sample['explainB'][:80]}...")
        print()

    # 3. CSV統合
    print("[3/3] CSVに統合")
    stats = merge_to_csv(explanations, CSV_PATH)

    # 結果レポート
    print("\n" + "="*80)
    print("抽出結果レポート")
    print("="*80)
    print(f"CSV総問題数:     {stats['total']}問")
    print(f"更新された問題:   {stats['updated']}問 ✅")
    print(f"スキップ:        {stats['skipped']}問")
    print("="*80)

    if stats['updated'] > 0:
        print("\n✅ R6年度学科B（35問）の解説文抽出完了！")
        print("   次のステップ:")
        print("   1. CSVをGoogle Sheetsにインポート")
        print("   2. Webアプリで表示を確認")
        print("   3. R6年度学科A（66問）は過去問サイトから収集")

    return explanations


if __name__ == '__main__':
    main()
