#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
フリガナと不要な問題番号を削除するスクリプト
"""
import csv
import sys
import re
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

CSV_PATH = Path(r"C:\ProgramData\Generative AI\Github\doboku-14w-training\tools\questionbank_drive_import.csv")

def clean_furigana_text(text):
    """フリガナと不要な要素を削除"""
    # 問題番号を削除（No.XX】または【No.XX】）
    text = re.sub(r'No\.\s*\d+】', '', text)
    text = re.sub(r'【No\.\s*\d+', '', text)

    # フリガナを削除（漢字1文字 + ひらがな1-3文字のパターン）
    # 例：「公こう」→「公」、「共きょう」→「共」
    text = re.sub(r'([\u4e00-\u9fff])([\u3040-\u309f]{1,3})(?=[\u4e00-\u9fff]|[\u3001-\u303f]|[\s\n]|$)', r'\1', text)

    # 先頭がひらがなの場合も削除（「こう公」→「公」）
    text = re.sub(r'([\u3040-\u309f]{1,3})([\u4e00-\u9fff])', r'\2', text)

    # ページ番号を削除（―11―など）
    text = re.sub(r'[―\-]+\s*\d+\s*[―\-]+', '', text)

    # DHP-A.smdなどのメタデータを削除
    text = re.sub(r'DHP-[AB]\.smd.*', '', text)

    # 連続する空白行を1つにまとめる
    text = re.sub(r'\n\n+', '\n\n', text)

    return text.strip()

# 穴埋め問題37件のqIdリスト
fill_in_qids = [
    'R3gakkaB-021', 'R3gakkaB-022', 'R3gakkaB-023', 'R3gakkaB-024',
    'R3gakkaB-025', 'R3gakkaB-026', 'R3gakkaB-027', 'R3gakkaB-028',
    'R3gakkaB-029', 'R3gakkaB-030', 'R3gakkaB-031', 'R3gakkaB-032',
    'R3gakkaB-033', 'R3gakkaB-034', 'R3gakkaB-035',
    'R4gakkaB-021', 'R4gakkaB-022', 'R4gakkaB-023', 'R4gakkaB-024',
    'R4gakkaB-025', 'R4gakkaB-026', 'R4gakkaB-027', 'R4gakkaB-028',
    'R4gakkaB-030', 'R4gakkaB-031', 'R4gakkaB-032', 'R4gakkaB-033',
    'R4gakkaB-034', 'R4gakkaB-035',
    'R5gakkaB-021', 'R5gakkaB-023', 'R5gakkaB-026', 'R5gakkaB-029',
    'R5gakkaB-033',
    'R6gakkaA-002',
    'R6gakkaB-021', 'R6gakkaB-023', 'R6gakkaB-033'
]

# CSVを読み込み
with open(CSV_PATH, 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    rows = list(reader)
    fieldnames = reader.fieldnames

updated_count = 0

# 各行のstemをクリーンアップ
for row in rows:
    if row['qId'] in fill_in_qids:
        original_stem = row['stem']

        # フリガナと不要要素を削除
        cleaned_stem = clean_furigana_text(original_stem)

        if cleaned_stem != original_stem:
            row['stem'] = cleaned_stem
            updated_count += 1
            print(f'✓ {row["qId"]}: クリーンアップ完了')

# CSVに書き戻し
with open(CSV_PATH, 'w', encoding='utf-8-sig', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print(f'\nクリーンアップ完了: {updated_count}件')
