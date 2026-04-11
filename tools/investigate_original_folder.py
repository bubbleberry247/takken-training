#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
原本フォルダー徹底調査スクリプト
説明文が本当に不足しているか、原本と抽出済みデータを比較検証
"""

import csv
import sys
import io
from collections import defaultdict
from pathlib import Path
from docx import Document

# UTF-8出力設定
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# パス設定
ORIGINAL_FOLDER = Path(r"C:\Users\masam\Downloads\１級土木-20260214T233348Z-1-001\１級土木")
EXTRACTION_CSV = Path(r"C:\ProgramData\Generative AI\Github\doboku-14w-training\data\explanations.csv")
OUTPUT_REPORT = Path(r"C:\ProgramData\Generative AI\Github\doboku-14w-training\tools\original_folder_investigation.md")
OUTPUT_GAPS = Path(r"C:\ProgramData\Generative AI\Github\doboku-14w-training\tools\extraction_gaps_detailed.csv")

def analyze_extraction_stats():
    """抽出済みデータの統計分析"""
    stats = defaultdict(lambda: {
        'total': 0,
        'has_explainLong': 0,
        'has_any_explain': 0,
        'has_choices': 0
    })

    with open(EXTRACTION_CSV, 'r', encoding='utf-8') as f:
        # 最初の行を読んで矢印を除去
        first_line = f.readline()
        if first_line.startswith('\ufeff'):  # BOM除去
            first_line = first_line[1:]
        # 矢印があれば除去
        if '→' in first_line:
            first_line = first_line.split('→')[1]

        # DictReaderを初期化
        f.seek(0)
        _ = f.readline()  # 元の行をスキップ

        reader = csv.DictReader(f, fieldnames=first_line.strip().split(','))
        for row in reader:
            qid = row['qId']
            year_segment = qid.split('-')[0]  # e.g., R1gakkaA

            stats[year_segment]['total'] += 1

            if row['explainLong'].strip():
                stats[year_segment]['has_explainLong'] += 1

            choice_count = sum([1 for field in ['explainA', 'explainB', 'explainC', 'explainD']
                               if row[field].strip()])
            if choice_count > 0:
                stats[year_segment]['has_choices'] += 1

            if any([row['explainA'].strip(), row['explainB'].strip(),
                    row['explainC'].strip(), row['explainD'].strip(),
                    row['explainShort'].strip(), row['explainLong'].strip()]):
                stats[year_segment]['has_any_explain'] += 1

    return stats

def analyze_word_files():
    """Word原本ファイルの分析"""
    files_info = []

    for file_path in ORIGINAL_FOLDER.glob("*.docx"):
        if file_path.name.startswith('~$'):  # 一時ファイルスキップ
            continue

        file_size = file_path.stat().st_size
        file_name = file_path.name

        # ファイル名から年度を抽出
        year_info = {
            'file_name': file_name,
            'file_path': str(file_path),
            'file_size': file_size,
            'year': None,
            'version': 'オリジナル'
        }

        # 年度抽出
        if '令和元年度' in file_name or '令和1年度' in file_name:
            year_info['year'] = 'R1'
        elif '令和2年度' in file_name:
            year_info['year'] = 'R2'
        elif '令和3年度' in file_name:
            year_info['year'] = 'R3'
        elif '令和4年度' in file_name:
            year_info['year'] = 'R4'
        elif '令和5年度' in file_name:
            year_info['year'] = 'R5'
        elif '令和6年度' in file_name:
            year_info['year'] = 'R6'
        elif '令和7年度' in file_name:
            year_info['year'] = 'R7'

        # バージョン判定
        if '(1)' in file_name:
            year_info['version'] = '(1)'
        elif '(2)' in file_name:
            year_info['version'] = '(2)'

        files_info.append(year_info)

    return sorted(files_info, key=lambda x: (x['year'] or '', x['version']))

def sample_word_content(file_path, max_paragraphs=10):
    """Word文書の内容をサンプリング"""
    try:
        doc = Document(file_path)
        paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]

        return {
            'total_paragraphs': len(paragraphs),
            'sample': paragraphs[:max_paragraphs],
            'success': True
        }
    except Exception as e:
        return {
            'total_paragraphs': 0,
            'sample': [],
            'success': False,
            'error': str(e)
        }

def main():
    print("=" * 80)
    print("原本フォルダー徹底調査")
    print("=" * 80)

    # 1. 抽出済みデータ統計
    print("\n## 1. 抽出済みデータ統計")
    stats = analyze_extraction_stats()

    print("\n| セグメント | 問題数 | 選択肢説明あり | まとめあり | Long抽出率 |")
    print("|------------|--------|----------------|------------|------------|")

    total_problems = 0
    total_with_long = 0

    for segment in sorted(stats.keys()):
        s = stats[segment]
        long_rate = (s['has_explainLong'] / s['total'] * 100) if s['total'] > 0 else 0
        print(f"| {segment} | {s['total']} | {s['has_choices']} | {s['has_explainLong']} | {long_rate:.1f}% |")
        total_problems += s['total']
        total_with_long += s['has_explainLong']

    overall_rate = (total_with_long / total_problems * 100) if total_problems > 0 else 0
    print(f"\n**合計**: {total_problems} 問中 {total_with_long} 問にまとめあり ({overall_rate:.1f}%)")

    # 2. 原本ファイル分析
    print("\n## 2. 原本Wordファイル分析")
    files_info = analyze_word_files()

    print("\n| 年度 | ファイル名 | サイズ | バージョン |")
    print("|------|-----------|--------|-----------|")

    for file_info in files_info:
        size_kb = file_info['file_size'] / 1024
        print(f"| {file_info['year']} | {file_info['file_name'][:40]}... | {size_kb:.1f} KB | {file_info['version']} |")

    # 3. 重複ファイル分析
    print("\n## 3. 重複ファイル比較")
    year_groups = defaultdict(list)
    for file_info in files_info:
        if file_info['year']:
            year_groups[file_info['year']].append(file_info)

    print("\n| 年度 | ファイル数 | 推奨ファイル | 理由 |")
    print("|------|-----------|-------------|------|")

    for year in sorted(year_groups.keys()):
        files = year_groups[year]
        if len(files) == 1:
            print(f"| {year} | 1 | オリジナル | 重複なし |")
        else:
            # 最大ファイルを推奨
            largest = max(files, key=lambda x: x['file_size'])
            size_diff = largest['file_size'] - min(f['file_size'] for f in files)
            diff_percent = (size_diff / largest['file_size']) * 100
            print(f"| {year} | {len(files)} | {largest['version']} | 最大サイズ (差分{diff_percent:.1f}%) |")

    # 4. Word内容サンプリング（令和3年度(2)の異常小ファイルを調査）
    print("\n## 4. 異常サイズファイルの内容確認")

    suspicious_files = [f for f in files_info if f['file_size'] < 20000]  # 20KB未満

    if suspicious_files:
        print(f"\n**{len(suspicious_files)} 件の小サイズファイルを検出**")
        for file_info in suspicious_files:
            print(f"\n### {file_info['file_name']}")
            print(f"- サイズ: {file_info['file_size']/1024:.1f} KB")

            content = sample_word_content(file_info['file_path'])
            if content['success']:
                print(f"- 段落数: {content['total_paragraphs']}")
                print(f"- サンプル:")
                for i, para in enumerate(content['sample'][:3], 1):
                    print(f"  {i}. {para[:100]}...")
            else:
                print(f"- エラー: {content['error']}")

    # 5. 詳細レポート保存
    print("\n## 5. 詳細レポート作成中...")

    with open(OUTPUT_REPORT, 'w', encoding='utf-8') as f:
        f.write("# 原本フォルダー徹底調査レポート\n\n")
        f.write(f"調査日時: 2026-02-16\n\n")

        f.write("## 調査概要\n\n")
        f.write(f"- 原本フォルダー: {ORIGINAL_FOLDER}\n")
        f.write(f"- 抽出済みデータ: {EXTRACTION_CSV}\n")
        f.write(f"- 総問題数: {total_problems} 問\n")
        f.write(f"- まとめ抽出率: {overall_rate:.1f}%\n\n")

        f.write("## ファイル一覧\n\n")
        for file_info in files_info:
            f.write(f"- {file_info['file_name']} ({file_info['file_size']/1024:.1f} KB)\n")

        f.write("\n## 推奨アクション\n\n")

        if overall_rate < 50:
            f.write("### 優先度：高\n")
            f.write("1. **大サイズファイル（令和7年度: 173KB）の詳細調査**\n")
            f.write("   - 最新年度で最大サイズ\n")
            f.write("   - 未抽出コンテンツが多数含まれている可能性\n\n")

            f.write("2. **重複ファイルの内容比較**\n")
            for year in ['R3', 'R4', 'R5', 'R6']:
                if year in year_groups and len(year_groups[year]) > 1:
                    f.write(f"   - {year}年度: {len(year_groups[year])} バージョン存在\n")
            f.write("\n")

            f.write("3. **小サイズファイルの確認**\n")
            if suspicious_files:
                for file_info in suspicious_files:
                    f.write(f"   - {file_info['file_name']} ({file_info['file_size']/1024:.1f} KB) → 不完全データの可能性\n")

    print(f"✓ レポート保存: {OUTPUT_REPORT}")

    # 6. 差分CSV作成
    with open(OUTPUT_GAPS, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['年度', 'セグメント', '問題数', 'まとめあり', '抽出率', '不足数', 'ステータス'])

        for segment in sorted(stats.keys()):
            s = stats[segment]
            year = segment[:2]  # R1, R2, etc.
            long_rate = (s['has_explainLong'] / s['total'] * 100) if s['total'] > 0 else 0
            missing = s['total'] - s['has_explainLong']
            status = 'OK' if long_rate >= 80 else '要確認' if long_rate >= 50 else '要抽出'

            writer.writerow([year, segment, s['total'], s['has_explainLong'],
                           f"{long_rate:.1f}%", missing, status])

    print(f"✓ 差分リスト保存: {OUTPUT_GAPS}")

    print("\n" + "=" * 80)
    print("調査完了")
    print("=" * 80)

if __name__ == '__main__':
    main()
