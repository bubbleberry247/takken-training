#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
詳細なコンテンツ分析

確認項目:
    1. 問題文（stem）がない問題
    2. 詳細解説文（explainA-D）がない問題
    3. 説明文が全くない問題（explainShort/A-D全て）
    4. 部分的な説明文がある問題
"""

import sys
import io
import csv
from pathlib import Path
from collections import defaultdict

# UTF-8出力設定
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

CSV_PATH = Path(r"C:\ProgramData\Generative AI\Github\doboku-14w-training\tools\questionbank_drive_import.csv")

def analyze_content():
    """詳細コンテンツ分析"""
    with open(CSV_PATH, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    total = len(rows)

    # カテゴリ別カウント
    no_stem = []                    # 問題文なし
    no_detail_explanation = []      # 詳細解説文なし（explainA-D全て空）
    no_any_explanation = []         # 説明文完全なし（explainShort/A-D全て空）
    has_short_only = []             # explainShortのみ（A-D全て空）
    has_partial_detail = []         # explainA-Dの一部のみ
    has_full_detail = []            # explainA-D全て存在

    for row in rows:
        qid = row.get('qId', '')
        stem = row.get('stem', '').strip()
        explain_short = row.get('explainShort', '').strip()
        explain_a = row.get('explainA', '').strip()
        explain_b = row.get('explainB', '').strip()
        explain_c = row.get('explainC', '').strip()
        explain_d = row.get('explainD', '').strip()

        # 問題文チェック
        if not stem:
            no_stem.append(qid)

        # 詳細解説文チェック
        has_a = bool(explain_a)
        has_b = bool(explain_b)
        has_c = bool(explain_c)
        has_d = bool(explain_d)

        detail_count = sum([has_a, has_b, has_c, has_d])

        if detail_count == 0:
            # explainA-D全て空
            no_detail_explanation.append(qid)

            if not explain_short:
                # explainShortも空
                no_any_explanation.append(qid)
            else:
                # explainShortのみ存在
                has_short_only.append(qid)

        elif detail_count == 4:
            # explainA-D全て存在
            has_full_detail.append(qid)
        else:
            # 一部のみ存在
            has_partial_detail.append(qid)

    # レポート出力
    print("=== 詳細コンテンツ分析 ===")
    print(f"総問題数: {total}問\n")

    print("【問題文（stem）】")
    print(f"  ✅ 問題文あり: {total - len(no_stem)}問 ({(total - len(no_stem))/total*100:.1f}%)")
    print(f"  ❌ 問題文なし: {len(no_stem)}問 ({len(no_stem)/total*100:.1f}%)")
    if no_stem:
        print(f"     問題文なしのqId: {no_stem[:10]}")
        if len(no_stem) > 10:
            print(f"     （他{len(no_stem)-10}問省略）")
    print()

    print("【詳細解説文（explainA-D）】")
    print(f"  ✅ 詳細解説文あり（A-D全て）: {len(has_full_detail)}問 ({len(has_full_detail)/total*100:.1f}%)")
    print(f"  ⚠️  部分的な詳細解説文: {len(has_partial_detail)}問 ({len(has_partial_detail)/total*100:.1f}%)")
    print(f"  ❌ 詳細解説文なし（A-D全て空）: {len(no_detail_explanation)}問 ({len(no_detail_explanation)/total*100:.1f}%)")
    print()

    print("【説明文全般】")
    print(f"  ✅ 詳細解説文あり（A-D全て）: {len(has_full_detail)}問 ({len(has_full_detail)/total*100:.1f}%)")
    print(f"  🟡 統合解説のみ（explainShortのみ）: {len(has_short_only)}問 ({len(has_short_only)/total*100:.1f}%)")
    print(f"  🔴 説明文完全欠落（Short/A-D全て空）: {len(no_any_explanation)}問 ({len(no_any_explanation)/total*100:.1f}%)")
    print()

    # 詳細リスト
    print("=" * 80)
    print("【詳細解説文がない問題（214問）の内訳】")
    print("=" * 80)
    print(f"\n🟡 統合解説のみ（explainShortのみ）: {len(has_short_only)}問")
    if has_short_only:
        # 年度別に分類
        by_year = defaultdict(list)
        for qid in has_short_only:
            year_segment = qid.split('-')[0]  # R7gakkaA
            by_year[year_segment].append(qid)

        for key in sorted(by_year.keys()):
            qids = by_year[key]
            print(f"  {key}: {len(qids)}問")

    print(f"\n🔴 説明文完全欠落: {len(no_any_explanation)}問")
    if no_any_explanation:
        # 年度別に分類
        by_year = defaultdict(list)
        for qid in no_any_explanation:
            year_segment = qid.split('-')[0]
            by_year[year_segment].append(qid)

        for key in sorted(by_year.keys()):
            qids = by_year[key]
            # 問題番号を抽出
            nums = [qid.split('-')[1] for qid in qids]
            nums_range = f"{min(nums)}〜{max(nums)}" if len(nums) > 1 else nums[0]
            print(f"  {key}: {len(qids)}問 ({nums_range})")

    print("\n" + "=" * 80)
    print("【サマリー】")
    print("=" * 80)
    print(f"問題文（stem）なし: {len(no_stem)}問")
    print(f"詳細解説文（explainA-D）なし: {len(no_detail_explanation)}問")
    print(f"  内訳:")
    print(f"    - 統合解説のみ（explainShortあり）: {len(has_short_only)}問")
    print(f"    - 説明文完全欠落（Short/A-D全て空）: {len(no_any_explanation)}問")
    print(f"説明文が何かしらある問題: {total - len(no_any_explanation)}問 ({(total - len(no_any_explanation))/total*100:.1f}%)")
    print(f"詳細解説文（A-D全て）がある問題: {len(has_full_detail)}問 ({len(has_full_detail)/total*100:.1f}%)")
    print("=" * 80)

    return {
        'no_stem': no_stem,
        'no_detail_explanation': no_detail_explanation,
        'no_any_explanation': no_any_explanation,
        'has_short_only': has_short_only,
        'has_partial_detail': has_partial_detail,
        'has_full_detail': has_full_detail,
    }


if __name__ == '__main__':
    analyze_content()
