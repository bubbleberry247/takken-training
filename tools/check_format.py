#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
フォーマット統一チェックツール
全682問のフォーマット統一性を検証し、問題箇所をレポート出力する

チェック項目:
1. 句読点の統一（読点「、」、句点「。」）
2. カッコの統一（全角「（）」と半角「()」の適切な使い分け）
3. 数値表記の統一（半角数字が基本）
4. 選択肢番号の統一（①②③④の使用）
"""

import csv
import re
from datetime import datetime
from typing import List, Dict, Tuple
import sys
import io

# UTF-8エンコーディング設定
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# チェック対象フィールド
TEXT_FIELDS = ['stem', 'choiceA', 'choiceB', 'choiceC', 'choiceD', 'choiceE',
               'explainA', 'explainB', 'explainC', 'explainD', 'explainE',
               'explainShort', 'explainLong']

class FormatIssue:
    """フォーマット問題を表すクラス"""
    def __init__(self, qid: str, field: str, issue_type: str,
                 position: str, current: str, recommended: str):
        self.qid = qid
        self.field = field
        self.issue_type = issue_type
        self.position = position
        self.current = current
        self.recommended = recommended

def check_punctuation_consistency(text: str, qid: str, field: str) -> List[FormatIssue]:
    """句読点の統一性チェック"""
    issues = []

    # 半角カンマの検出（全角「、」が期待される文脈）
    # 日本語文中のカンマを検出
    pattern = r'([ぁ-んァ-ヶー一-龯]),([ぁ-んァ-ヶー一-龯])'
    for match in re.finditer(pattern, text):
        pos = match.start()
        context = text[max(0, pos-10):min(len(text), pos+20)]
        issues.append(FormatIssue(
            qid, field, '読点の不統一',
            f'位置{pos}付近: "{context}"',
            ',（半角カンマ）',
            '、（全角読点）'
        ))

    # 半角ピリオドの検出（文末の句点として使われている場合）
    # 日本語文末のピリオドを検出
    pattern = r'([ぁ-んァ-ヶー一-龯])\.$'
    if re.search(pattern, text):
        pos = len(text) - 1
        context = text[max(0, pos-15):]
        issues.append(FormatIssue(
            qid, field, '句点の不統一',
            f'文末: "{context}"',
            '.（半角ピリオド）',
            '。（全角句点）'
        ))

    return issues

def check_bracket_consistency(text: str, qid: str, field: str) -> List[FormatIssue]:
    """カッコの統一性チェック"""
    issues = []

    # 日本語文中の半角カッコ検出（全角が期待される）
    # ただし、英数字のみの場合は半角でOK
    pattern = r'([ぁ-んァ-ヶー一-龯])\(([^)]*)\)([ぁ-んァ-ヶー一-龯])'
    for match in re.finditer(pattern, text):
        pos = match.start()
        context = text[max(0, pos-10):min(len(text), pos+30)]
        issues.append(FormatIssue(
            qid, field, 'カッコの不統一',
            f'位置{pos}付近: "{context}"',
            '()（半角カッコ）',
            '（）（全角カッコ）'
        ))

    # 英数字のみでない内容の半角カッコをチェック
    pattern = r'\(([^)]*[ぁ-んァ-ヶー一-龯][^)]*)\)'
    for match in re.finditer(pattern, text):
        pos = match.start()
        context = text[max(0, pos-10):min(len(text), pos+30)]
        issues.append(FormatIssue(
            qid, field, 'カッコの不統一',
            f'位置{pos}付近: "{context}"',
            '()（日本語含む半角カッコ）',
            '（）（全角カッコ）'
        ))

    return issues

def check_number_consistency(text: str, qid: str, field: str) -> List[FormatIssue]:
    """数値表記の統一性チェック"""
    issues = []

    # 全角数字の検出（半角が期待される）
    full_width_numbers = re.findall(r'[０-９]+', text)
    if full_width_numbers:
        for match_obj in re.finditer(r'[０-９]+', text):
            pos = match_obj.start()
            context = text[max(0, pos-10):min(len(text), pos+20)]
            full_num = match_obj.group()
            # 全角→半角変換
            half_num = full_num.translate(str.maketrans('０１２３４５６７８９', '0123456789'))
            issues.append(FormatIssue(
                qid, field, '数値表記の不統一',
                f'位置{pos}付近: "{context}"',
                f'{full_num}（全角数字）',
                f'{half_num}（半角数字）'
            ))

    # パーセント記号の全角チェック
    if '％' in text:
        for match_obj in re.finditer(r'％', text):
            pos = match_obj.start()
            context = text[max(0, pos-10):min(len(text), pos+10)]
            issues.append(FormatIssue(
                qid, field, '単位表記の不統一',
                f'位置{pos}付近: "{context}"',
                '％（全角パーセント）',
                '%（半角パーセント）'
            ))

    return issues

def check_choice_number_format(text: str, qid: str, field: str) -> List[FormatIssue]:
    """選択肢番号フォーマットチェック"""
    issues = []

    # 選択肢フィールドでない場合、問題文中の選択肢参照をチェック
    # ①②③④ 以外の丸数字を検出
    unexpected_circles = re.findall(r'[⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳]', text)
    if unexpected_circles:
        for match_obj in re.finditer(r'[⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳]', text):
            pos = match_obj.start()
            context = text[max(0, pos-10):min(len(text), pos+20)]
            issues.append(FormatIssue(
                qid, field, '選択肢番号の不統一',
                f'位置{pos}付近: "{context}"',
                f'{match_obj.group()}（想定外の丸数字）',
                '①②③④のいずれか、または組合せ表記を確認'
            ))

    # 半角数字+ピリオド形式の選択肢番号（例: "1. "）を検出
    # これは選択肢フィールドの冒頭で使われていることがある
    if field.startswith('choice') and re.match(r'^[1-4]\.\s', text):
        issues.append(FormatIssue(
            qid, field, '選択肢番号の不統一',
            '選択肢冒頭',
            '数字+ピリオド形式（例: "1. "）',
            '番号なし（または①②③④）'
        ))

    return issues

def check_format(csv_path: str) -> List[FormatIssue]:
    """CSVファイルの全行をチェック"""
    all_issues = []

    with open(csv_path, 'r', encoding='utf-8', newline='') as f:
        reader = csv.DictReader(f)

        for row_num, row in enumerate(reader, start=2):  # ヘッダーは1行目
            qid = row.get('qId', f'Row{row_num}')

            for field in TEXT_FIELDS:
                text = row.get(field, '')
                if not text or text.strip() == '':
                    continue

                # 各種チェック実行
                all_issues.extend(check_punctuation_consistency(text, qid, field))
                all_issues.extend(check_bracket_consistency(text, qid, field))
                all_issues.extend(check_number_consistency(text, qid, field))
                all_issues.extend(check_choice_number_format(text, qid, field))

    return all_issues

def generate_report(issues: List[FormatIssue], output_path: str):
    """チェック結果をCSVレポート出力"""
    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        fieldnames = ['qId', 'field', 'issue_type', 'position', 'current', 'recommended']
        writer = csv.DictWriter(f, fieldnames=fieldnames)

        writer.writeheader()
        for issue in issues:
            writer.writerow({
                'qId': issue.qid,
                'field': issue.field,
                'issue_type': issue.issue_type,
                'position': issue.position,
                'current': issue.current,
                'recommended': issue.recommended
            })

    print(f"レポートを出力しました: {output_path}")
    print(f"検出された問題数: {len(issues)}")

def print_summary(issues: List[FormatIssue]):
    """問題タイプ別のサマリー表示"""
    issue_counts = {}
    for issue in issues:
        issue_type = issue.issue_type
        issue_counts[issue_type] = issue_counts.get(issue_type, 0) + 1

    print("\n【問題タイプ別サマリー】")
    for issue_type, count in sorted(issue_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {issue_type}: {count}件")

    # qId別の問題数トップ10
    qid_counts = {}
    for issue in issues:
        qid = issue.qid
        qid_counts[qid] = qid_counts.get(qid, 0) + 1

    print("\n【問題数が多いqId トップ10】")
    for qid, count in sorted(qid_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"  {qid}: {count}件")

def main():
    csv_path = 'C:/ProgramData/Generative AI/Github/doboku-14w-training/tools/questionbank_drive_import.csv'
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_path = f'C:/ProgramData/Generative AI/Github/doboku-14w-training/tools/format_check_report_{timestamp}.csv'

    print("=" * 60)
    print("フォーマット統一チェック開始")
    print("=" * 60)
    print(f"対象ファイル: {csv_path}")
    print()

    # チェック実行
    issues = check_format(csv_path)

    # レポート出力
    generate_report(issues, output_path)

    # サマリー表示
    print_summary(issues)

    print("\n" + "=" * 60)
    print("チェック完了")
    print("=" * 60)

if __name__ == '__main__':
    main()
