#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
questionbank_drive_import.csvの説明文不足状況を分析

出力:
    - 選択肢説明（explainA-D）の充足率
    - 統合解説（explainShort）の充足率
    - 年度別・セグメント別の内訳
    - 不足問題のリスト
"""

import sys
import io
import csv
from pathlib import Path
from collections import defaultdict

# UTF-8出力設定
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

CSV_PATH = Path(r"C:\ProgramData\Generative AI\Github\doboku-14w-training\tools\questionbank_drive_import.csv")

def analyze_csv():
    """CSVを分析"""
    with open(CSV_PATH, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    total = len(rows)
    print(f"=== 説明文不足状況分析 ===")
    print(f"総問題数: {total}問\n")

    # カテゴリ別カウント
    has_choice_explain = 0  # explainA-D全て存在
    has_short_explain = 0    # explainShortのみ
    has_no_explain = 0       # 説明文なし

    # 部分的な説明文
    partial_explain = 0      # explainA-Dの一部のみ

    # 年度別・セグメント別
    by_year_segment = defaultdict(lambda: {
        'total': 0,
        'has_choice': 0,
        'has_short': 0,
        'has_none': 0,
    })

    # 不足問題リスト
    missing_choice = []  # 選択肢説明なし
    missing_all = []     # 全説明文なし

    for row in rows:
        qid = row.get('qId', '')
        segment = row.get('segmentId', '')

        # 年度抽出（例: R7gakkaA-001 → R7）
        year = qid[:2] if qid else ''

        # 選択肢説明の存在チェック
        has_a = bool(row.get('explainA', '').strip())
        has_b = bool(row.get('explainB', '').strip())
        has_c = bool(row.get('explainC', '').strip())
        has_d = bool(row.get('explainD', '').strip())

        all_choice = has_a and has_b and has_c and has_d
        some_choice = has_a or has_b or has_c or has_d

        # 統合解説の存在チェック
        has_short = bool(row.get('explainShort', '').strip())

        # カテゴリ分類
        if all_choice:
            has_choice_explain += 1
            by_year_segment[f"{year}-{segment}"]['has_choice'] += 1
        elif has_short:
            has_short_explain += 1
            by_year_segment[f"{year}-{segment}"]['has_short'] += 1
            missing_choice.append(qid)
        else:
            has_no_explain += 1
            by_year_segment[f"{year}-{segment}"]['has_none'] += 1
            missing_all.append(qid)

        if some_choice and not all_choice:
            partial_explain += 1

        by_year_segment[f"{year}-{segment}"]['total'] += 1

    # サマリー出力
    print("【全体サマリー】")
    print(f"  ✅ 選択肢説明完備（explainA-D全て）: {has_choice_explain}問 ({has_choice_explain/total*100:.1f}%)")
    print(f"  🟡 統合解説のみ（explainShort）: {has_short_explain}問 ({has_short_explain/total*100:.1f}%)")
    print(f"  ❌ 説明文なし: {has_no_explain}問 ({has_no_explain/total*100:.1f}%)")
    if partial_explain > 0:
        print(f"  ⚠️  部分的な選択肢説明: {partial_explain}問")
    print()

    # 年度別・セグメント別
    print("【年度別・セグメント別】")
    for key in sorted(by_year_segment.keys()):
        data = by_year_segment[key]
        print(f"  {key:15s}: 総{data['total']:3d}問 | "
              f"選択肢説明{data['has_choice']:3d}問 ({data['has_choice']/data['total']*100:5.1f}%) | "
              f"統合のみ{data['has_short']:3d}問 | "
              f"説明なし{data['has_none']:3d}問")
    print()

    # 不足問題リスト
    print("【選択肢説明不足問題（統合解説のみ）】")
    if missing_choice:
        print(f"  総数: {len(missing_choice)}問")
        # 年度別グルーピング
        by_year = defaultdict(list)
        for qid in missing_choice:
            year_segment = qid.split('-')[0]  # R7gakkaA
            by_year[year_segment].append(qid)

        for year_segment in sorted(by_year.keys()):
            qids = by_year[year_segment]
            # 問題番号を抽出（R7gakkaA-001 → 001）
            nums = [qid.split('-')[1] for qid in qids]
            nums_range = f"{min(nums)}〜{max(nums)}" if len(nums) > 1 else nums[0]
            print(f"  - {year_segment}: {len(qids)}問 ({nums_range})")
    else:
        print("  なし ✅")
    print()

    print("【説明文完全欠落問題】")
    if missing_all:
        print(f"  総数: {len(missing_all)}問")
        for qid in missing_all:
            print(f"  - {qid}")
    else:
        print("  なし ✅")
    print()

    # 推奨アクション
    print("【推奨アクション】")
    if has_no_explain > 0:
        print(f"  🔴 高優先: 説明文完全欠落（{has_no_explain}問）→ 早急に追加推奨")
    if has_short_explain > 0:
        print(f"  🟡 中優先: 統合解説のみ（{has_short_explain}問）→ 選択肢別説明の追加を検討")
        print(f"     Claude for Chrome収集で対応可能（現在24/155問完了、残り{has_short_explain}問）")
    if has_choice_explain == total:
        print(f"  ✅ 全問題に選択肢説明完備！")

    print()
    print("【次のステップ】")
    if has_no_explain == 0 and has_short_explain < 100:
        print("  1. 現在のデータでGoogle Sheetsにインポート（推奨）")
        print("  2. Webアプリで動作確認")
        print("  3. 必要に応じて残り説明文の収集を継続")
    elif has_short_explain >= 100:
        print(f"  1. Claude for Chrome収集を継続（残り{has_short_explain}問）")
        print("  2. 定期的にCSV統合 & Google Sheetsインポート")
        print("  3. Webアプリで動作確認")


if __name__ == '__main__':
    analyze_csv()
