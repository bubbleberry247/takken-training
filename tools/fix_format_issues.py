#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
フォーマット統一修正ツール
検出された問題を自動修正する

主な修正内容:
1. 日本語文中の半角カンマ「,」→ 全角読点「、」
2. 日本語文末の半角ピリオド「.」→ 全角句点「。」
3. 日本語文中の半角カッコ「()」→ 全角カッコ「（）」（日本語を含む場合）
4. 全角数字 → 半角数字
5. 全角パーセント「％」→ 半角パーセント「%」
"""

import csv
import re
from datetime import datetime
import sys
import io

# UTF-8エンコーディング設定
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# チェック対象フィールド
TEXT_FIELDS = ['stem', 'choiceA', 'choiceB', 'choiceC', 'choiceD', 'choiceE',
               'explainA', 'explainB', 'explainC', 'explainD', 'explainE',
               'explainShort', 'explainLong']

class FixStats:
    """修正統計を保持するクラス"""
    def __init__(self):
        self.comma_fixed = 0
        self.period_fixed = 0
        self.bracket_fixed = 0
        self.number_fixed = 0
        self.percent_fixed = 0

    def total(self):
        return (self.comma_fixed + self.period_fixed + self.bracket_fixed +
                self.number_fixed + self.percent_fixed)

    def __str__(self):
        return f"""修正統計:
  読点修正（,→、）: {self.comma_fixed}件
  句点修正（.→。）: {self.period_fixed}件
  カッコ修正（()→（））: {self.bracket_fixed}件
  数字修正（全角→半角）: {self.number_fixed}件
  パーセント修正（％→%）: {self.percent_fixed}件
  合計: {self.total()}件"""

def fix_punctuation(text: str, stats: FixStats) -> str:
    """句読点の修正"""
    original = text

    # 日本語文中の半角カンマ → 全角読点
    # パターン: 日本語文字 + , + 日本語文字
    pattern = r'([ぁ-んァ-ヶー一-龯]),([ぁ-んァ-ヶー一-龯])'
    text = re.sub(pattern, r'\1、\2', text)

    # 日本語文末の半角ピリオド → 全角句点
    pattern = r'([ぁ-んァ-ヶー一-龯])\.$'
    text = re.sub(pattern, r'\1。', text)

    # 統計更新
    if text != original:
        comma_count = original.count(',') - text.count(',')
        period_count = original.count('.') - text.count('.')
        stats.comma_fixed += comma_count
        stats.period_fixed += period_count

    return text

def fix_brackets(text: str, stats: FixStats) -> str:
    """カッコの修正（日本語を含む半角カッコを全角に）"""
    original = text
    modified = text

    # パターン1: 日本語文字の前後に半角カッコ
    pattern = r'([ぁ-んァ-ヶー一-龯])\(([^)]*)\)([ぁ-んァ-ヶー一-龯])'
    modified = re.sub(pattern, r'\1(\2)\3', modified)

    # パターン2: カッコ内に日本語を含む場合は全角カッコに
    # 複数回実行して入れ子も処理
    for _ in range(3):  # 最大3階層の入れ子まで対応
        pattern = r'\(([^()]*[ぁ-んァ-ヶー一-龯][^()]*)\)'
        new_text = re.sub(pattern, r'(\1)', modified)
        if new_text == modified:
            break
        modified = new_text

    # 統計更新
    if modified != original:
        # 簡易的なカウント（完全ではないが目安として）
        bracket_count = original.count('(') - modified.count('(')
        stats.bracket_fixed += bracket_count

    return modified

def fix_numbers(text: str, stats: FixStats) -> str:
    """数値表記の修正"""
    original = text

    # 全角数字 → 半角数字
    full_width = '０１２３４５６７８９'
    half_width = '0123456789'
    trans_table = str.maketrans(full_width, half_width)
    text = text.translate(trans_table)

    # 全角パーセント → 半角パーセント
    text = text.replace('％', '%')

    # 統計更新
    if text != original:
        # 全角数字のカウント
        number_count = sum(original.count(c) for c in full_width)
        stats.number_fixed += number_count

        # パーセント記号のカウント
        percent_count = original.count('％')
        stats.percent_fixed += percent_count

    return text

def fix_text_field(text: str, stats: FixStats) -> str:
    """テキストフィールドの総合修正"""
    if not text or text.strip() == '':
        return text

    # 各種修正を順次適用
    text = fix_punctuation(text, stats)
    text = fix_brackets(text, stats)
    text = fix_numbers(text, stats)

    return text

def fix_csv(input_path: str, output_path: str) -> FixStats:
    """CSVファイルの修正"""
    stats = FixStats()
    rows = []

    with open(input_path, 'r', encoding='utf-8', newline='') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames

        for row in reader:
            # テキストフィールドを修正
            for field in TEXT_FIELDS:
                if field in row:
                    row[field] = fix_text_field(row[field], stats)
            rows.append(row)

    # 修正結果を出力
    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return stats

def main():
    input_path = 'C:/ProgramData/Generative AI/Github/doboku-14w-training/tools/questionbank_drive_import.csv'
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = f'C:/ProgramData/Generative AI/Github/doboku-14w-training/tools/questionbank_drive_import_backup_{timestamp}.csv'
    output_path = input_path  # 元のファイルを上書き

    print("=" * 60)
    print("フォーマット統一修正開始")
    print("=" * 60)
    print(f"入力ファイル: {input_path}")
    print(f"バックアップ: {backup_path}")
    print()

    # バックアップ作成
    import shutil
    shutil.copy2(input_path, backup_path)
    print(f"✓ バックアップ作成完了")

    # 修正実行
    stats = fix_csv(input_path, output_path)

    print(f"\n✓ 修正完了")
    print(f"出力ファイル: {output_path}")
    print()
    print(stats)

    print("\n" + "=" * 60)
    print("修正完了")
    print("=" * 60)

if __name__ == '__main__':
    main()
