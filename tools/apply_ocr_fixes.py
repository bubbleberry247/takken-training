#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OCR誤変換修正スクリプト

ocr_fix_report.md で特定された誤変換を修正
"""

import sys
import io
import csv
import os
from datetime import datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

CSV_FILE = r"C:\ProgramData\Generative AI\Github\doboku-14w-training\tools\questionbank_drive_import.csv"
BACKUP_FILE = r"C:\ProgramData\Generative AI\Github\doboku-14w-training\tools\questionbank_drive_import_backup_{timestamp}.csv"
OUTPUT_FILE = r"C:\ProgramData\Generative AI\Github\doboku-14w-training\tools\questionbank_drive_import_fixed.csv"

def load_csv(filepath):
    """CSVファイルを読み込む"""
    rows = []
    with open(filepath, 'r', encoding='utf-8', newline='') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for row in reader:
            rows.append(row)
    return rows, fieldnames

def save_csv(filepath, rows, fieldnames):
    """CSVファイルを保存"""
    with open(filepath, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

def apply_fixes(rows):
    """修正を適用"""
    fixes_applied = {
        '分数欠落': 0,
        '範囲開始値欠落': 0,
        '全角数字': 0,
        '表記ゆれ': 0,
    }

    text_columns = ['stem', 'choiceA', 'choiceB', 'choiceC', 'choiceD', 'choiceE',
                   'explainA', 'explainB', 'explainC', 'explainD', 'explainE',
                   'explainShort', 'explainLong']

    for idx, row in enumerate(rows, start=2):  # CSVの行番号は2から
        qid = row.get('qId', '')

        # P1-1: 分数欠落の修正
        if idx == 29 and qid == 'R1gakkaA-028':
            old = row['choiceA']
            row['choiceA'] = old.replace('層の仕上り厚の/以 下', '層の仕上り厚の1/3以下')
            if row['choiceA'] != old:
                fixes_applied['分数欠落'] += 1
                print(f"[行{idx}] 分数欠落修正: {qid} choiceA")

        if idx == 121 and qid == 'R2gakkaA-024':
            old = row['choiceD']
            row['choiceD'] = old.replace('その/以上が地下', 'その2/3以上が地下')
            if row['choiceD'] != old:
                fixes_applied['分数欠落'] += 1
                print(f"[行{idx}] 分数欠落修正: {qid} choiceD")

        if idx == 347 and qid == 'R4gakkaA-058':
            old = row['choiceD']
            row['choiceD'] = old.replace('20分の/以上', '20分の1以上')
            if row['choiceD'] != old:
                fixes_applied['分数欠落'] += 1
                print(f"[行{idx}] 分数欠落修正: {qid} choiceD")

        # P1-2: 範囲開始値欠落の修正
        if idx == 30 and qid == 'R1gakkaA-029':
            old = row['choiceB']
            row['choiceB'] = old.replace('縦継目側の 〜10 cm', '縦継目側の 5〜10 cm')
            if row['choiceB'] != old:
                fixes_applied['範囲開始値欠落'] += 1
                print(f"[行{idx}] 範囲開始値欠落修正: {qid} choiceB")

        if idx == 104 and qid == 'R2gakkaA-007':
            old = row['choiceD']
            row['choiceD'] = old.replace('m 当たり 〜10 kg', 'm³当たり 5〜10 kg')
            if row['choiceD'] != old:
                fixes_applied['範囲開始値欠落'] += 1
                print(f"[行{idx}] 範囲開始値欠落修正: {qid} choiceD")

        if idx == 28 and qid == 'R1gakkaA-027':
            old = row['choiceD']
            row['choiceD'] = old.replace('CBR が未満', 'CBR が3未満')
            if row['choiceD'] != old:
                fixes_applied['範囲開始値欠落'] += 1
                print(f"[行{idx}] 範囲開始値欠落修正: {qid} choiceD")

        # P1-3: 全角数字の修正
        for col in text_columns:
            old = row[col]
            # 全角数字を半角に変換
            new = old
            new = new.replace('０', '0')
            new = new.replace('１', '1')
            new = new.replace('２', '2')
            new = new.replace('３', '3')
            new = new.replace('４', '4')
            new = new.replace('５', '5')
            new = new.replace('６', '6')
            new = new.replace('７', '7')
            new = new.replace('８', '8')
            new = new.replace('９', '9')

            if new != old:
                row[col] = new
                fixes_applied['全角数字'] += 1
                print(f"[行{idx}] 全角数字修正: {qid} {col}")

        # P2: 表記ゆれ「締め固め」→「締固め」
        for col in text_columns:
            old = row[col]
            new = old.replace('締め固め', '締固め')
            if new != old:
                row[col] = new
                fixes_applied['表記ゆれ'] += 1
                # 表記ゆれは大量にあるので個別ログは出力しない

    return fixes_applied

def main():
    print("=" * 80)
    print("OCR誤変換修正スクリプト")
    print("=" * 80)
    print()

    # バックアップ作成
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = BACKUP_FILE.format(timestamp=timestamp)

    import shutil
    shutil.copy2(CSV_FILE, backup_file)
    print(f"バックアップ作成: {backup_file}")
    print()

    # CSV読み込み
    print("CSVファイル読み込み中...")
    rows, fieldnames = load_csv(CSV_FILE)
    print(f"総行数: {len(rows)}行")
    print()

    # 修正適用
    print("修正適用中...")
    fixes_applied = apply_fixes(rows)
    print()

    # 結果保存
    save_csv(OUTPUT_FILE, rows, fieldnames)
    print(f"修正済みファイル保存: {OUTPUT_FILE}")
    print()

    # サマリー表示
    print("=" * 80)
    print("修正サマリー")
    print("=" * 80)
    for category, count in fixes_applied.items():
        print(f"{category}: {count}件")
    print()
    print(f"合計修正箇所: {sum(fixes_applied.values())}件")
    print()
    print("修正完了!")
    print()
    print("次のステップ:")
    print(f"1. 修正内容を確認: {OUTPUT_FILE}")
    print(f"2. 問題なければ元ファイルを置換: copy \"{OUTPUT_FILE}\" \"{CSV_FILE}\"")
    print(f"3. バックアップは保存: {backup_file}")

if __name__ == "__main__":
    main()
