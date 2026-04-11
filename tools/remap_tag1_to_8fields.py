#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
QuestionBankのtag1を8分野に統一するスクリプト
既存のtag1はtag2に移動し、問題番号から新しいtag1を自動設定
"""
import csv
import re

def extract_question_number(qId, source_ref):
    """
    qIdまたはsource_refから問題番号を抽出

    Returns: (part, number)
        part: 'AM' (午前) or 'PM' (午後)
        number: 問題番号（1-44 or 1-28）
    """
    # source_refから抽出を試みる（例：R1 学科A No.1）
    if source_ref:
        match = re.search(r'学科([AB])\s+No\.(\d+)', source_ref)
        if match:
            part = 'AM' if match.group(1) == 'A' else 'PM'
            number = int(match.group(2))
            return (part, number)

    # qIdから抽出を試みる（例：R1gakkaA-001）
    if qId:
        match = re.search(r'gakka([AB])-0*(\d+)', qId)
        if match:
            part = 'AM' if match.group(1) == 'A' else 'PM'
            number = int(match.group(2))
            return (part, number)

    return (None, None)

def map_to_8fields(part, number):
    """
    問題番号から8分野に分類

    Returns: tag1名
    """
    if part == 'AM':
        # 新形式（R6-R7）：No.1-44
        if 1 <= number <= 14:
            return '土木工学等'
        elif 15 <= number <= 20:
            return '設備等'
        elif 21 <= number <= 33:
            return '躯体'
        elif 34 <= number <= 44:
            return '仕上げ'
        # 旧形式（R1-R5）：No.45-66を分類
        elif 45 <= number <= 54:
            return '土木工学等'  # 追加分は土木工学等に分類
        elif 55 <= number <= 66:
            return '土木工学等'  # 追加分は土木工学等に分類
    elif part == 'PM':
        # 新形式：No.1-28
        if 1 <= number <= 10:
            return '施工管理'
        elif 11 <= number <= 20:
            return '法規'
        elif 21 <= number <= 26:
            return '施工管理法(応用)'
        elif 27 <= number <= 28:
            return '施工管理法'
        # 旧形式：No.29-35を分類
        elif 29 <= number <= 35:
            return '施工管理法'  # 追加分は施工管理法に分類

    return ''  # 分類できない場合は空

def main():
    input_file = 'questionbank_drive_import.csv'
    output_file = 'questionbank_drive_import_8fields.csv'

    # CSVを読み込み
    with open(input_file, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    print(f"読み込み: {len(rows)}件")

    # 統計情報
    stats = {
        '土木工学等': 0,
        '設備等': 0,
        '躯体': 0,
        '仕上げ': 0,
        '施工管理': 0,
        '法規': 0,
        '施工管理法(応用)': 0,
        '施工管理法': 0,
        '分類不可': 0
    }

    # 各行を処理
    for row in rows:
        qId = row.get('qId', '')
        source_ref = row.get('source_ref', '')
        old_tag1 = row.get('tag1', '')
        old_tag2 = row.get('tag2', '')

        # 問題番号を抽出
        part, number = extract_question_number(qId, source_ref)

        # 8分野に分類
        new_tag1 = map_to_8fields(part, number)

        # 既存のtag1をtag2に移動（tag2が空の場合のみ）
        if old_tag1 and not old_tag2:
            row['tag2'] = old_tag1

        # 新しいtag1を設定
        row['tag1'] = new_tag1

        # 統計
        if new_tag1:
            stats[new_tag1] += 1
        else:
            stats['分類不可'] += 1

    # CSVを出力
    with open(output_file, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\n出力: {output_file}")
    print(f"\n=== 8分野への分類結果 ===")
    for field, count in stats.items():
        print(f"{field}: {count}件")

    print(f"\n合計: {sum(stats.values())}件")

if __name__ == '__main__':
    main()
