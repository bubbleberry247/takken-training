#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
穴埋め問題の誤変換修正スクリプト

OCRで (イ)(ロ)(ハ)(ニ) が Q, R, S などに誤変換された問題を修正する。
"""

import csv
import re
import sys
from pathlib import Path

def fix_stem(stem: str) -> str:
    """問題文(stem)の空欄記号を修正"""

    # パターン1: "のQ〜R" → "の(イ)〜(ニ)"
    stem = re.sub(r'のQ〜R', 'の(イ)〜(ニ)', stem)

    # パターン2: "のR〜S" → "の(イ)〜(ニ)"
    stem = re.sub(r'のR〜S', 'の(イ)〜(ニ)', stem)

    # パターン3: 孤立した " Q " → " (イ) "
    stem = re.sub(r'\sQ\s', ' (イ) ', stem)

    # パターン4: 孤立した " R " → " (ロ) " または文脈依存
    # ※ ただし "R1", "R2" などの年度表記は除外
    stem = re.sub(r'(?<!R)\sR\s(?![0-9])', ' (ロ) ', stem)

    # パターン5: 孤立した " S " → " (ハ) "
    stem = re.sub(r'\sS\s', ' (ハ) ', stem)

    # パターン6: 文末の " S 。" → " (ニ)。"
    stem = re.sub(r'\sS\s?。', ' (ニ)。', stem)

    return stem


def fix_choice(choice: str, debug=False) -> str:
    """選択肢を読みやすく整形"""

    if not choice or choice.strip() == '':
        return choice

    original = choice

    # 全角括弧を半角に変換
    choice = choice.replace('（イ）', '(イ)')
    choice = choice.replace('（ロ）', '(ロ)')
    choice = choice.replace('（ハ）', '(ハ)')
    choice = choice.replace('（ニ）', '(ニ)')

    if debug and choice != original:
        print(f"  [DEBUG] 全角→半角変換後: {choice[:80]}")

    # 誤変換された Q, R, S, T を削除
    # パターン: "(イ)Q(ロ)S(ハ)R(ニ)..." → "(イ)(ロ)(ハ)(ニ)..."
    before_qrst = choice
    choice = re.sub(r'\(イ\)[QRST](?=\()', '(イ)', choice)
    choice = re.sub(r'\(ロ\)[QRST](?=\()', '(ロ)', choice)
    choice = re.sub(r'\(ハ\)[QRST](?=\()', '(ハ)', choice)
    choice = re.sub(r'\(ニ\)[QRST](?=\()', '(ニ)', choice)

    if debug and choice != before_qrst:
        print(f"  [DEBUG] QRST削除後: {choice[:80]}")

    # 選択肢の空欄記号の前にスペースを追加（見やすくする）
    # ただし、直前が閉じ括弧 ) の場合（つまり、直前が別の空欄記号の場合）はスペースを入れない
    choice = re.sub(r'(?<!\))\(ロ\)', '  (ロ)', choice)
    choice = re.sub(r'(?<!\))\(ハ\)', '  (ハ)', choice)
    choice = re.sub(r'(?<!\))\(ニ\)', '  (ニ)', choice)

    # 連続スペースを2つに統一
    choice = re.sub(r'\s{3,}', '  ', choice)

    # 先頭・末尾の余分なスペースを除去
    choice = choice.strip()

    return choice


def process_csv(input_file: Path, output_file: Path) -> dict:
    """CSVファイルを処理"""

    stats = {
        'total_rows': 0,
        'fixed_stems': 0,
        'fixed_choices': 0,
        'fixed_rows': [],
        'warnings': []
    }

    with open(input_file, 'r', encoding='utf-8-sig') as f_in:  # BOMを自動で除去
        reader = csv.DictReader(f_in)
        fieldnames = reader.fieldnames
        rows = list(reader)

    for i, row in enumerate(rows, start=2):  # CSVは2行目から（1行目はヘッダー）
        stats['total_rows'] += 1

        # 空行またはqIdが欠けている行をスキップ
        if not row.get('qId') or not row.get('stem'):
            continue

        original_stem = row['stem']
        original_choices = [row.get('choiceA', ''), row.get('choiceB', ''),
                           row.get('choiceC', ''), row.get('choiceD', '')]

        # 問題文を修正
        fixed_stem = fix_stem(row['stem'])
        if fixed_stem != original_stem:
            row['stem'] = fixed_stem
            stats['fixed_stems'] += 1
            stats['fixed_rows'].append({
                'row': i,
                'qId': row['qId'],
                'type': 'stem'
            })

        # 選択肢を修正
        choice_fixed = False
        has_qrst = False
        for choice_key in ['choiceA', 'choiceB', 'choiceC', 'choiceD']:
            if choice_key in row:
                original = row[choice_key]

                # Q, R, S, T が含まれているか警告
                if re.search(r'\([イロハニ]\)[QRST]', original):
                    has_qrst = True

                fixed = fix_choice(original)
                if fixed != original:
                    row[choice_key] = fixed
                    choice_fixed = True

        if choice_fixed:
            stats['fixed_choices'] += 1
            stats['fixed_rows'].append({
                'row': i,
                'qId': row['qId'],
                'type': 'choices'
            })

        if has_qrst:
            stats['warnings'].append({
                'row': i,
                'qId': row['qId'],
                'message': '選択肢に Q/R/S/T が含まれています（誤変換の可能性）'
            })

    # 修正後のCSVを出力
    with open(output_file, 'w', encoding='utf-8', newline='') as f_out:
        writer = csv.DictWriter(f_out, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return stats


def main():
    # ファイルパス
    script_dir = Path(__file__).parent
    input_file = script_dir / 'questionbank_drive_import.csv'
    output_file = script_dir / 'questionbank_drive_import_fixed.csv'

    print("=" * 60)
    print("穴埋め問題 誤変換修正スクリプト")
    print("=" * 60)
    print()
    print(f"入力ファイル: {input_file}")
    print(f"出力ファイル: {output_file}")
    print()

    if not input_file.exists():
        print(f"エラー: 入力ファイルが見つかりません: {input_file}")
        sys.exit(1)

    # 処理実行
    print("処理中...")
    stats = process_csv(input_file, output_file)

    # 結果表示
    print()
    print("=" * 60)
    print("処理完了")
    print("=" * 60)
    print(f"総行数:           {stats['total_rows']}")
    print(f"問題文を修正:     {stats['fixed_stems']} 問")
    print(f"選択肢を修正:     {stats['fixed_choices']} 問")
    print()

    if stats['fixed_rows']:
        print("修正した問題:")
        for item in stats['fixed_rows'][:20]:  # 最初の20件を表示
            print(f"  行 {item['row']:4d}: {item['qId']:20s} ({item['type']})")

        if len(stats['fixed_rows']) > 20:
            print(f"  ... 他 {len(stats['fixed_rows']) - 20} 件")

    print()
    print(f"修正後のファイル: {output_file}")
    print()

    # 警告表示
    if stats['warnings']:
        print("=" * 60)
        print("⚠️  警告")
        print("=" * 60)
        for warn in stats['warnings'][:10]:
            print(f"  行 {warn['row']:4d}: {warn['qId']:20s}")
            print(f"         {warn['message']}")
        if len(stats['warnings']) > 10:
            print(f"  ... 他 {len(stats['warnings']) - 10} 件")
        print()


if __name__ == '__main__':
    main()
