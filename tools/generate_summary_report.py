#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
データ統計サマリーレポート生成スクリプト
全682問の統計情報を詳細に分析
"""

import csv
import sys
import io
from datetime import datetime
from collections import defaultdict, Counter

# UTF-8出力対応
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def main():
    input_file = 'questionbank_drive_import.csv'

    print("=" * 80)
    print("データ統計サマリーレポート")
    print(f"生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    print()

    # 統計データ収集用
    total_count = 0
    segment_stats = defaultdict(int)
    type_stats = defaultdict(int)
    difficulty_stats = defaultdict(int)
    tag1_stats = defaultdict(int)
    status_stats = defaultdict(int)
    has_explanation_count = 0
    has_image_count = 0
    has_choice_image_count = 0
    choice_type_stats = defaultdict(int)
    year_stats = defaultdict(int)

    # CSVファイル読み込み（BOM対応）
    with open(input_file, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)

        for row in reader:
            total_count += 1

            # セグメント統計
            segmentId = row.get('segmentId', '').strip()
            if segmentId:
                segment_stats[segmentId] += 1

                # 年度別統計
                year = segmentId[:2] if len(segmentId) >= 2 else 'Unknown'
                year_stats[year] += 1

            # タイプ統計
            type_val = row.get('type', '').strip()
            if type_val:
                type_stats[type_val] += 1

            # 難易度統計
            difficulty = row.get('difficulty', '').strip()
            if difficulty:
                difficulty_stats[difficulty] += 1

            # タグ1統計
            tag1 = row.get('tag1', '').strip()
            if tag1:
                tag1_stats[tag1] += 1

            # ステータス統計
            status = row.get('status', '').strip()
            if status:
                status_stats[status] += 1

            # 解説の有無
            explain_short = row.get('explainShort', '').strip()
            explain_long = row.get('explainLong', '').strip()
            if explain_short or explain_long:
                has_explanation_count += 1

            # 画像の有無
            image_url = row.get('imageUrl', '').strip()
            if image_url:
                has_image_count += 1

            # 選択肢画像の有無
            choice_image_url = row.get('choiceImageUrl', '').strip()
            if choice_image_url:
                has_choice_image_count += 1

            # 選択肢タイプ
            has_e = row.get('choiceE', '').strip() != ''
            if has_e:
                choice_type_stats['5択'] += 1
            else:
                choice_type_stats['4択'] += 1

    # レポート出力
    print(f"【全体統計】")
    print(f"  総問題数: {total_count}問")
    print(f"  ユニークセグメント数: {len(segment_stats)}セグメント")
    print()

    print(f"【年度別問題数】")
    for year in sorted(year_stats.keys()):
        count = year_stats[year]
        percentage = (count / total_count * 100) if total_count > 0 else 0
        print(f"  {year}年度: {count}問 ({percentage:.1f}%)")
    print()

    print(f"【セグメント別問題数（上位10件）】")
    sorted_segments = sorted(segment_stats.items(), key=lambda x: x[1], reverse=True)
    for i, (segment, count) in enumerate(sorted_segments[:10], 1):
        percentage = (count / total_count * 100) if total_count > 0 else 0
        print(f"  {i}. {segment}: {count}問 ({percentage:.1f}%)")
    print()

    print(f"【選択肢タイプ別】")
    for choice_type in sorted(choice_type_stats.keys()):
        count = choice_type_stats[choice_type]
        percentage = (count / total_count * 100) if total_count > 0 else 0
        print(f"  {choice_type}: {count}問 ({percentage:.1f}%)")
    print()

    print(f"【問題タイプ別】")
    for type_val in sorted(type_stats.keys()):
        count = type_stats[type_val]
        percentage = (count / total_count * 100) if total_count > 0 else 0
        print(f"  {type_val}: {count}問 ({percentage:.1f}%)")
    if not type_stats:
        print(f"  （データなし）")
    print()

    print(f"【難易度別】")
    for difficulty in sorted(difficulty_stats.keys()):
        count = difficulty_stats[difficulty]
        percentage = (count / total_count * 100) if total_count > 0 else 0
        print(f"  レベル{difficulty}: {count}問 ({percentage:.1f}%)")
    if not difficulty_stats:
        print(f"  （データなし）")
    print()

    print(f"【カテゴリー別（tag1）上位10件】")
    sorted_tags = sorted(tag1_stats.items(), key=lambda x: x[1], reverse=True)
    for i, (tag, count) in enumerate(sorted_tags[:10], 1):
        percentage = (count / total_count * 100) if total_count > 0 else 0
        print(f"  {i}. {tag}: {count}問 ({percentage:.1f}%)")
    print()

    print(f"【ステータス別】")
    for status in sorted(status_stats.keys()):
        count = status_stats[status]
        percentage = (count / total_count * 100) if total_count > 0 else 0
        print(f"  {status}: {count}問 ({percentage:.1f}%)")
    print()

    print(f"【コンテンツ充実度】")
    explain_percentage = (has_explanation_count / total_count * 100) if total_count > 0 else 0
    image_percentage = (has_image_count / total_count * 100) if total_count > 0 else 0
    choice_image_percentage = (has_choice_image_count / total_count * 100) if total_count > 0 else 0

    print(f"  解説あり: {has_explanation_count}問 ({explain_percentage:.1f}%)")
    print(f"  問題画像あり: {has_image_count}問 ({image_percentage:.1f}%)")
    print(f"  選択肢画像あり: {has_choice_image_count}問 ({choice_image_percentage:.1f}%)")
    print()

    print("=" * 80)
    print("レポート生成完了")
    print("=" * 80)

if __name__ == '__main__':
    main()
