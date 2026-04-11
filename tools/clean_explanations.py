#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
説明文CSVのクリーニングスクリプト
広告スクリプトやノイズテキストを削除する
"""

import csv
import re
import sys
import io
from datetime import datetime
from pathlib import Path

# Windows環境でのUTF-8出力設定
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 削除対象のパターン（正規表現）
NOISE_PATTERNS = [
    r'Advertisement',
    r'\(adsbygoogle\s*=\s*window\.adsbygoogle\s*\|\|\s*\[\]\)\.push\(\{\}\);?',
    r'window\.adsbygoogle',
    r'adsbygoogle',
    r'<script[^>]*>.*?</script>',  # スクリプトタグ
    r'参考になった数\d+',  # "参考になった数36" のようなパターン
    r'参考になった\s+参考にならなかった',
    r'この解説の修正を提案する',
]

# 対象カラム（説明文フィールド）
TARGET_COLUMNS = ['explainA', 'explainB', 'explainC', 'explainD', 'explainShort', 'explainLong']


def clean_text(text: str) -> str:
    """
    テキストをクリーニングする

    Args:
        text: クリーニング対象のテキスト

    Returns:
        クリーニング後のテキスト
    """
    if not text or text.strip() == '':
        return text

    original = text

    # 各ノイズパターンを削除
    for pattern in NOISE_PATTERNS:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.DOTALL)

    # 複数の空白を1つにまとめる
    text = re.sub(r'\s+', ' ', text)

    # 前後の空白をトリム
    text = text.strip()

    return text


def clean_explanations_csv(input_path: Path, output_path: Path = None, backup: bool = True) -> dict:
    """
    説明文CSVをクリーニングする

    Args:
        input_path: 入力CSVファイルのパス
        output_path: 出力CSVファイルのパス（Noneの場合は上書き）
        backup: バックアップを作成するかどうか

    Returns:
        クリーニング結果の統計情報
    """
    input_path = Path(input_path)

    # 出力先が指定されていない場合は上書き
    if output_path is None:
        output_path = input_path
    else:
        output_path = Path(output_path)

    # バックアップ作成
    if backup:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = input_path.parent / f"{input_path.stem}_backup_{timestamp}{input_path.suffix}"

        # バックアップをコピー
        import shutil
        shutil.copy2(input_path, backup_path)
        print(f"[OK] バックアップ作成: {backup_path}")

    # 統計情報
    stats = {
        'total_rows': 0,
        'cleaned_rows': 0,
        'cleaned_fields': 0,
        'by_column': {col: 0 for col in TARGET_COLUMNS}
    }

    # CSVを読み込み
    rows = []
    with open(input_path, 'r', encoding='utf-8', newline='') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames

        for row in reader:
            stats['total_rows'] += 1
            row_cleaned = False

            # 各対象カラムをクリーニング
            for col in TARGET_COLUMNS:
                if col in row:
                    original = row[col]
                    cleaned = clean_text(original)

                    if original != cleaned:
                        row[col] = cleaned
                        stats['cleaned_fields'] += 1
                        stats['by_column'][col] += 1
                        row_cleaned = True

            if row_cleaned:
                stats['cleaned_rows'] += 1

            rows.append(row)

    # クリーニング済みCSVを書き込み
    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return stats


def main():
    """メイン処理"""
    # パス設定
    project_root = Path(r'C:\ProgramData\Generative AI\Github\doboku-14w-training')
    input_csv = project_root / 'data' / 'explanations.csv'

    print("=" * 60)
    print("説明文CSVクリーニングツール")
    print("=" * 60)
    print(f"入力ファイル: {input_csv}")
    print()

    # クリーニング実行
    stats = clean_explanations_csv(input_csv, backup=True)

    # 結果レポート
    print()
    print("=" * 60)
    print("クリーニング結果")
    print("=" * 60)
    print(f"総行数: {stats['total_rows']}")
    print(f"クリーニング済み行数: {stats['cleaned_rows']}")
    print(f"クリーニング済みフィールド数: {stats['cleaned_fields']}")
    print()
    print("カラム別修正件数:")
    for col, count in stats['by_column'].items():
        if count > 0:
            print(f"  - {col}: {count}件")
    print("=" * 60)
    print(f"[OK] クリーニング完了: {input_csv}")
    print()


if __name__ == '__main__':
    main()
