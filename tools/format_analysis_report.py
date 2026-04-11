#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
フォーマット問題の詳細分析レポート生成
問題タイプごとの具体例を抽出して、修正前の確認を行う
"""

import csv
import sys
import io

# UTF-8エンコーディング設定
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

def analyze_report(report_path: str):
    """レポートファイルの分析"""

    # 問題タイプごとの例を収集
    examples = {
        '読点の不統一': [],
        'カッコの不統一': [],
        '数値表記の不統一': [],
        '単位表記の不統一': [],
        '選択肢番号の不統一': []
    }

    qid_counts = {}

    with open(report_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        for row in reader:
            issue_type = row['issue_type']
            qid = row['qId']

            # 問題タイプごとの例を収集（最大5件まで）
            if issue_type in examples and len(examples[issue_type]) < 5:
                examples[issue_type].append({
                    'qId': qid,
                    'field': row['field'],
                    'position': row['position'],
                    'current': row['current'],
                    'recommended': row['recommended']
                })

            # qId別カウント
            qid_counts[qid] = qid_counts.get(qid, 0) + 1

    # レポート出力
    print("=" * 80)
    print("フォーマット問題 詳細分析レポート")
    print("=" * 80)
    print()

    for issue_type, items in examples.items():
        if not items:
            continue

        print(f"\n【{issue_type}】 ({len(items)}件の例)")
        print("-" * 80)

        for i, item in enumerate(items, 1):
            print(f"\n例{i}: {item['qId']} ({item['field']})")
            print(f"  箇所: {item['position']}")
            print(f"  現状: {item['current']}")
            print(f"  推奨: {item['recommended']}")

    # 問題が多いqIdのトップ20
    print("\n" + "=" * 80)
    print("【問題が多いqId トップ20】")
    print("-" * 80)

    sorted_qids = sorted(qid_counts.items(), key=lambda x: x[1], reverse=True)[:20]
    for rank, (qid, count) in enumerate(sorted_qids, 1):
        print(f"{rank:2d}. {qid:20s} : {count:3d}件")

    print("\n" + "=" * 80)

def main():
    report_path = 'C:/ProgramData/Generative AI/Github/doboku-14w-training/tools/format_check_report_20260216_105543.csv'

    print("レポートファイル:", report_path)
    print()

    analyze_report(report_path)

if __name__ == '__main__':
    main()
