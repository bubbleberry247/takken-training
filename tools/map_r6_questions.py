#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
R6年度のWordファイルから問題IDとqIdのマッピングを作成

目的:
    - ファイル内の問題番号（問1〜69）
    - 実際のID（78561〜）
    - 実際の問題番号（問70など）
    - qId（R6gakkaA-XXX, R6gakkaB-XXX）
を正確にマッピングする
"""

import sys
import io
from pathlib import Path
from docx import Document
import re

# UTF-8出力設定
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

FILE_PATH = Path(r"C:\Users\masam\Downloads\１級土木-20260214T233348Z-1-001\１級土木\1級土木 解説文集 令和6年度.docx")

def extract_r6_mapping():
    """
    R6年度の問題マッピングを抽出
    """
    doc = Document(FILE_PATH)

    mappings = []

    current_file_q = None
    current_id = None
    current_actual_q = None
    current_segment = None

    for para in doc.paragraphs:
        text = para.text.strip()
        if not text:
            continue

        # 問題番号とID（例: 問4（ID: 78564））
        match_q_id = re.search(r'問(\d+)[\s（]*ID[：:\s]*(\d+)', text)
        if match_q_id:
            current_file_q = int(match_q_id.group(1))
            current_id = int(match_q_id.group(2))
            current_actual_q = None
            current_segment = None

        # 実際の問題番号（例: 【問70（問題B ユニットe 問4）】）
        match_actual = re.search(r'【問(\d+)[\s（]*問題([AB])', text)
        if match_actual and current_id:
            current_actual_q = int(match_actual.group(1))
            current_segment = match_actual.group(2)

            # qIdを計算
            if current_segment == 'A':
                qid = f"R6gakkaA-{current_actual_q:03d}"
            else:
                # 学科Bは問67〜101なので、67を引いて1ベースに変換
                qid_num = current_actual_q - 66
                qid = f"R6gakkaB-{qid_num:03d}"

            mappings.append({
                'file_q': current_file_q,
                'id': current_id,
                'actual_q': current_actual_q,
                'segment': current_segment,
                'qid': qid,
            })

            # リセット
            current_file_q = None
            current_id = None
            current_actual_q = None
            current_segment = None

    return mappings


def main():
    print("=== R6年度 問題マッピング ===\n")

    mappings = extract_r6_mapping()

    print(f"検出された問題数: {len(mappings)}問\n")

    # マッピングテーブル表示
    print("| ファイル内問題番号 | ID | 実際の問題番号 | 学科 | qId |")
    print("|-------------------|------|--------------|------|-----|")

    for m in mappings[:20]:  # 最初の20問を表示
        print(f"| 問{m['file_q']} | {m['id']} | 問{m['actual_q']} | {m['segment']} | {m['qid']} |")

    if len(mappings) > 20:
        print(f"| ... | ... | ... | ... | ... |")
        print(f"（残り{len(mappings) - 20}問省略）")

    # 統計
    print("\n【統計】")
    gakka_a = [m for m in mappings if m['segment'] == 'A']
    gakka_b = [m for m in mappings if m['segment'] == 'B']

    print(f"学科A: {len(gakka_a)}問")
    if gakka_a:
        print(f"  問題番号範囲: 問{min(m['actual_q'] for m in gakka_a)}〜問{max(m['actual_q'] for m in gakka_a)}")
        print(f"  qId範囲: {min(m['qid'] for m in gakka_a)} 〜 {max(m['qid'] for m in gakka_a)}")

    print(f"学科B: {len(gakka_b)}問")
    if gakka_b:
        print(f"  問題番号範囲: 問{min(m['actual_q'] for m in gakka_b)}〜問{max(m['actual_q'] for m in gakka_b)}")
        print(f"  qId範囲: {min(m['qid'] for m in gakka_b)} 〜 {max(m['qid'] for m in gakka_b)}")

    # ID範囲確認
    print(f"\nID範囲: {min(m['id'] for m in mappings)} 〜 {max(m['id'] for m in mappings)}")

    # マッピングをJSONで保存
    import json
    output_file = Path(__file__).parent / "r6_mapping.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(mappings, f, ensure_ascii=False, indent=2)

    print(f"\n✓ マッピング保存: {output_file.name}")

    return mappings


if __name__ == '__main__':
    main()
