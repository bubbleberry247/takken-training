#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
説明文欠損分析スクリプト
セグメント別・問題別の説明文充足率を分析
"""
import csv
import sys
from pathlib import Path
from collections import defaultdict

# 標準出力のエンコーディング設定（Windows対応）
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def analyze_explanation_gaps(csv_path):
    """説明文欠損の分析"""
    segment_stats = defaultdict(lambda: {'total_fields': 0, 'filled_fields': 0, 'questions': []})

    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)

        for row in reader:
            qid = row.get('qId', '')
            segment_id = row.get('segmentId', '')

            # 各問題の説明文充足率を計算
            explain_fields = ['explainA', 'explainB', 'explainC', 'explainD']
            filled_count = sum(1 for field in explain_fields if row.get(field, '').strip())
            total_count = 4  # A-Dの4つ

            segment_stats[segment_id]['total_fields'] += total_count
            segment_stats[segment_id]['filled_fields'] += filled_count
            segment_stats[segment_id]['questions'].append({
                'qId': qid,
                'filled': filled_count,
                'total': total_count,
                'rate': filled_count / total_count * 100
            })

    # セグメント別充足率でソート
    sorted_segments = sorted(
        segment_stats.items(),
        key=lambda x: x[1]['filled_fields'] / x[1]['total_fields'] if x[1]['total_fields'] > 0 else 0
    )

    print("=" * 80)
    print("説明文充足率分析（セグメント別）")
    print("=" * 80)
    print(f"{'セグメントID':<20} {'問題数':>6} {'充足率':>8} {'充足数/総数':>12}")
    print("-" * 80)

    for segment_id, stats in sorted_segments:
        total = stats['total_fields']
        filled = stats['filled_fields']
        rate = filled / total * 100 if total > 0 else 0
        q_count = len(stats['questions'])

        print(f"{segment_id:<20} {q_count:>6} {rate:>7.1f}% {filled:>5}/{total:<5}")

    # 充足率0%のセグメントを抽出
    print("\n" + "=" * 80)
    print("説明文が全く設定されていないセグメント")
    print("=" * 80)

    zero_segments = [seg for seg, stats in sorted_segments
                     if stats['filled_fields'] == 0]

    if zero_segments:
        for seg in zero_segments:
            q_count = len(segment_stats[seg]['questions'])
            print(f"  - {seg}: {q_count}問")
    else:
        print("  なし（全セグメントで少なくとも1つ以上の説明あり）")

    # 充足率100%のセグメント
    print("\n" + "=" * 80)
    print("説明文が完全に設定されているセグメント（充足率100%）")
    print("=" * 80)

    full_segments = [seg for seg, stats in sorted_segments
                     if stats['filled_fields'] == stats['total_fields'] and stats['total_fields'] > 0]

    if full_segments:
        for seg in full_segments:
            q_count = len(segment_stats[seg]['questions'])
            print(f"  - {seg}: {q_count}問")
    else:
        print("  なし")

    # 総合統計
    total_fields = sum(stats['total_fields'] for stats in segment_stats.values())
    total_filled = sum(stats['filled_fields'] for stats in segment_stats.values())
    overall_rate = total_filled / total_fields * 100 if total_fields > 0 else 0

    print("\n" + "=" * 80)
    print("総合統計")
    print("=" * 80)
    print(f"総セグメント数: {len(segment_stats)}")
    print(f"総問題数: {sum(len(stats['questions']) for stats in segment_stats.values())}")
    print(f"総説明文フィールド数: {total_fields}（問題数 × 4選択肢）")
    print(f"設定済み説明文数: {total_filled}")
    print(f"未設定説明文数: {total_fields - total_filled}")
    print(f"全体充足率: {overall_rate:.1f}%")

    # CSV出力（セグメント別）
    output_path = Path(csv_path).parent / 'explanation_gaps_by_segment.csv'
    with open(output_path, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['segmentId', 'q_count', 'filled_fields', 'total_fields', 'rate'])

        for segment_id, stats in sorted_segments:
            total = stats['total_fields']
            filled = stats['filled_fields']
            rate = filled / total * 100 if total > 0 else 0
            q_count = len(stats['questions'])
            writer.writerow([segment_id, q_count, filled, total, f'{rate:.1f}'])

    print(f"\nセグメント別レポート出力: {output_path}")

def main():
    csv_path = Path(__file__).parent / 'questionbank_drive_import.csv'

    if not csv_path.exists():
        print(f"エラー: ファイルが見つかりません: {csv_path}")
        sys.exit(1)

    analyze_explanation_gaps(csv_path)

if __name__ == '__main__':
    main()
