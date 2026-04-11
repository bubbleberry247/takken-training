#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
タグ付け統計レポート生成スクリプト
"""

import csv
import sys
import io
from collections import defaultdict

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def generate_report(csv_file):
    """統計レポートを生成"""
    
    with open(csv_file, 'r', encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    # 統計カウンター
    tag1_count = defaultdict(int)
    tag2_count = defaultdict(int)
    tag3_count = defaultdict(int)
    tag1_tag2_matrix = defaultdict(lambda: defaultdict(int))
    
    total = 0
    for row in rows:
        qid = row.get('qId', '')
        if not qid or qid == 'qId' or qid.startswith('・'):
            continue
        
        tag1 = row.get('tag1', '')
        tag2 = row.get('tag2', '')
        tag3 = row.get('tag3', '')
        
        if tag1:
            tag1_count[tag1] += 1
        if tag2:
            tag2_count[tag2] += 1
        if tag3:
            tag3_count[tag3] += 1
        if tag1 and tag2:
            tag1_tag2_matrix[tag1][tag2] += 1
        
        total += 1
    
    print("="*80)
    print("【1級土木施工管理技士 問題銀行タグ付け統計レポート】")
    print("="*80)
    print(f"\n総問題数: {total}問\n")
    
    print("\n" + "="*80)
    print("■ tag1 (主要分野) 分布")
    print("="*80)
    for category, count in sorted(tag1_count.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / total) * 100
        print(f"  {category:25s}: {count:4d}問 ({percentage:5.1f}%)")
    
    print("\n" + "="*80)
    print("■ tag2 (サブ分野) 分布 TOP30")
    print("="*80)
    for i, (subcategory, count) in enumerate(sorted(tag2_count.items(), key=lambda x: x[1], reverse=True)[:30], 1):
        percentage = (count / total) * 100
        print(f"  {i:2d}. {subcategory:25s}: {count:4d}問 ({percentage:5.1f}%)")
    
    print("\n" + "="*80)
    print("■ tag3 (年度) 分布")
    print("="*80)
    for year, count in sorted(tag3_count.items()):
        percentage = (count / total) * 100
        print(f"  {year:15s}: {count:4d}問 ({percentage:5.1f}%)")
    
    print("\n" + "="*80)
    print("■ tag1 × tag2 マトリクス (主要3分野)")
    print("="*80)
    
    # 上位3分野のマトリクス表示
    top3_tag1 = sorted(tag1_count.items(), key=lambda x: x[1], reverse=True)[:3]
    for tag1, count in top3_tag1:
        print(f"\n【{tag1}】 ({count}問)")
        for tag2, cnt in sorted(tag1_tag2_matrix[tag1].items(), key=lambda x: x[1], reverse=True):
            percentage = (cnt / count) * 100
            print(f"    - {tag2:25s}: {cnt:3d}問 ({percentage:5.1f}%)")
    
    print("\n" + "="*80)

if __name__ == "__main__":
    csv_file = r"C:\ProgramData\Generative AI\Github\doboku-14w-training\tools\questionbank_drive_import.csv"
    generate_report(csv_file)
