#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
データ整合性検証スクリプト
全682問のデータ整合性を検証する

検証項目:
1. 必須フィールドの欠落チェック (qId, segmentId, stem, correct)
2. 選択肢数の統一確認 (4択: A-D, 5択: A-E)
3. 年度・セグメント情報の検証 (qId/segmentIdの整合性)
4. source_refの形式統一確認
5. テキスト品質の検証（文字化け、異常な文字など）
6. メタデータフィールドの検証 (type, difficulty, status)

使用方法:
  python check_integrity.py

出力:
  - コンソールに検証結果サマリーを表示
  - integrity_check_report_{timestamp}.csv にエラーレポートを出力
"""

import csv
import sys
import io
import re
from datetime import datetime
from collections import defaultdict

# UTF-8出力対応
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 必須フィールド定義
REQUIRED_FIELDS = ['qId', 'segmentId', 'stem', 'correct']

# 選択肢フィールド定義
CHOICE_FIELDS = ['choiceA', 'choiceB', 'choiceC', 'choiceD', 'choiceE']

# qIdパターン定義
QID_PATTERN = re.compile(r'^R\d+gakka[AB]-\d{3}$')

def validate_required_fields(row, row_num):
    """必須フィールドの欠落チェック"""
    errors = []

    for field in REQUIRED_FIELDS:
        if not row.get(field) or row[field].strip() == '':
            errors.append({
                'row': row_num,
                'qId': row.get('qId', 'N/A'),
                'field': field,
                'issue': '必須フィールドが空',
                'severity': 'ERROR',
                'recommendation': f'{field}を入力してください'
            })

    return errors

def validate_choice_consistency(row, row_num):
    """選択肢数の統一確認"""
    errors = []
    qId = row.get('qId', 'N/A')

    # 選択肢の存在確認
    choices = {}
    for choice in CHOICE_FIELDS:
        choices[choice] = row.get(choice, '').strip() != ''

    # 4択問題（A-D）の検証
    has_a_d = all([choices['choiceA'], choices['choiceB'],
                   choices['choiceC'], choices['choiceD']])
    has_e = choices['choiceE']

    if not has_a_d:
        # A-Dが揃っていない
        missing = [c for c in ['choiceA', 'choiceB', 'choiceC', 'choiceD']
                   if not choices[c]]
        errors.append({
            'row': row_num,
            'qId': qId,
            'field': ', '.join(missing),
            'issue': '4択問題として選択肢が不足',
            'severity': 'ERROR',
            'recommendation': f'不足している選択肢を追加: {", ".join(missing)}'
        })

    # 5択問題の場合、choiceEが適切に設定されているか
    if has_e and not has_a_d:
        errors.append({
            'row': row_num,
            'qId': qId,
            'field': 'choiceE',
            'issue': '5択問題だがA-Dが不完全',
            'severity': 'ERROR',
            'recommendation': 'A-Dの選択肢を先に補完してください'
        })

    # correctフィールドと選択肢の整合性
    correct = row.get('correct', '').strip()
    if correct:
        if correct not in ['A', 'B', 'C', 'D', 'E']:
            errors.append({
                'row': row_num,
                'qId': qId,
                'field': 'correct',
                'issue': f'正解記号が不正: {correct}',
                'severity': 'ERROR',
                'recommendation': 'A, B, C, D, Eのいずれかを指定してください'
            })
        elif correct == 'E' and not has_e:
            errors.append({
                'row': row_num,
                'qId': qId,
                'field': 'correct',
                'issue': '正解がEだがchoiceEが空',
                'severity': 'ERROR',
                'recommendation': 'choiceEを入力してください'
            })
        elif correct != 'E' and not choices.get(f'choice{correct}', False):
            errors.append({
                'row': row_num,
                'qId': qId,
                'field': 'correct',
                'issue': f'正解が{correct}だがchoice{correct}が空',
                'severity': 'ERROR',
                'recommendation': f'choice{correct}を入力してください'
            })

    return errors

def validate_qid_format(row, row_num):
    """qIdフォーマットの検証"""
    errors = []
    qId = row.get('qId', '').strip()

    if qId and not QID_PATTERN.match(qId):
        errors.append({
            'row': row_num,
            'qId': qId,
            'field': 'qId',
            'issue': 'qIdのフォーマットが不正',
            'severity': 'WARNING',
            'recommendation': '形式: R{年度}gakka{A|B}-{3桁番号} (例: R1gakkaA-001)'
        })

    return errors

def validate_segment_consistency(row, row_num):
    """segmentIdとqIdの整合性確認"""
    errors = []
    qId = row.get('qId', '').strip()
    segmentId = row.get('segmentId', '').strip()

    if qId and segmentId:
        # qIdからsegmentIdを抽出（R1gakkaA-001 → R1gakkaA）
        expected_segment = '-'.join(qId.split('-')[:-1])

        if segmentId != expected_segment:
            errors.append({
                'row': row_num,
                'qId': qId,
                'field': 'segmentId',
                'issue': f'segmentIdとqIdが不整合 (期待値: {expected_segment}, 実際: {segmentId})',
                'severity': 'ERROR',
                'recommendation': f'segmentIdを {expected_segment} に修正してください'
            })

    return errors

def validate_source_ref_format(row, row_num):
    """source_refの形式統一確認"""
    errors = []
    source_ref = row.get('source_ref', '').strip()

    if source_ref:
        # 期待される形式: R1 学科A No.1
        pattern = re.compile(r'^R\d+\s学科[AB]\sNo\.\d+$')
        if not pattern.match(source_ref):
            errors.append({
                'row': row_num,
                'qId': row.get('qId', 'N/A'),
                'field': 'source_ref',
                'issue': f'source_refの形式が非標準: {source_ref}',
                'severity': 'WARNING',
                'recommendation': '形式: R{年度} 学科{A|B} No.{番号} (例: R1 学科A No.1)'
            })

    return errors

def validate_text_quality(row, row_num):
    """テキスト品質の検証（文字化け、異常な文字など）"""
    errors = []
    qId = row.get('qId', 'N/A')

    # 検証対象フィールド
    text_fields = {
        'stem': '問題文',
        'choiceA': '選択肢A',
        'choiceB': '選択肢B',
        'choiceC': '選択肢C',
        'choiceD': '選択肢D',
        'choiceE': '選択肢E',
        'explainShort': '短い解説',
        'explainLong': '詳細解説'
    }

    # 組合せ問題の検出（問題文に「組合せ」「組み合わせ」が含まれる）
    stem = row.get('stem', '')
    is_combination_question = '組合せ' in stem or '組み合わせ' in stem

    for field, label in text_fields.items():
        text = row.get(field, '').strip()
        if not text:
            continue

        # 異常に短いテキスト（1文字のみ）
        if len(text) == 1 and field in ['stem', 'choiceA', 'choiceB', 'choiceC', 'choiceD']:
            errors.append({
                'row': row_num,
                'qId': qId,
                'field': field,
                'issue': f'{label}が1文字のみ（異常な可能性）',
                'severity': 'WARNING',
                'recommendation': f'{label}の内容を確認してください'
            })

        # 数字のみ（選択肢で数字のみは異常だが、組合せ問題は除外）
        if field.startswith('choice') and text.isdigit() and not is_combination_question:
            errors.append({
                'row': row_num,
                'qId': qId,
                'field': field,
                'issue': f'{label}が数字のみ',
                'severity': 'WARNING',
                'recommendation': f'{label}の内容を確認してください'
            })

    return errors

def validate_metadata_fields(row, row_num):
    """メタデータフィールドの検証"""
    errors = []
    qId = row.get('qId', 'N/A')

    # typeフィールドの検証
    valid_types = ['knowledge', 'application', 'comprehension']
    type_val = row.get('type', '').strip()
    if type_val and type_val not in valid_types:
        errors.append({
            'row': row_num,
            'qId': qId,
            'field': 'type',
            'issue': f'typeフィールドの値が非標準: {type_val}',
            'severity': 'INFO',
            'recommendation': f'標準値: {", ".join(valid_types)}'
        })

    # difficultyフィールドの検証
    difficulty = row.get('difficulty', '').strip()
    if difficulty and not difficulty.isdigit():
        errors.append({
            'row': row_num,
            'qId': qId,
            'field': 'difficulty',
            'issue': f'difficultyが数値ではない: {difficulty}',
            'severity': 'WARNING',
            'recommendation': '難易度は数値（1-5）で指定してください'
        })
    elif difficulty and int(difficulty) not in range(1, 6):
        errors.append({
            'row': row_num,
            'qId': qId,
            'field': 'difficulty',
            'issue': f'difficultyの範囲が異常: {difficulty}',
            'severity': 'INFO',
            'recommendation': '難易度は通常1-5の範囲です'
        })

    # statusフィールドの検証
    valid_statuses = ['published', 'draft', 'archived']
    status = row.get('status', '').strip()
    if status and status not in valid_statuses:
        errors.append({
            'row': row_num,
            'qId': qId,
            'field': 'status',
            'issue': f'statusフィールドの値が非標準: {status}',
            'severity': 'INFO',
            'recommendation': f'標準値: {", ".join(valid_statuses)}'
        })

    return errors

def main():
    input_file = 'questionbank_drive_import.csv'
    report_file = f'integrity_check_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'

    print(f"データ整合性検証開始: {input_file}")
    print("-" * 80)

    all_errors = []
    row_count = 0
    qid_set = set()
    qid_duplicates = []
    segment_stats = defaultdict(int)
    choice_type_stats = defaultdict(int)

    # CSVファイル読み込み（BOM対応）
    with open(input_file, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)

        for row_num, row in enumerate(reader, start=2):  # ヘッダーを除くため2から開始
            row_count += 1

            # qId重複チェック
            qId = row.get('qId', '').strip()
            if qId:
                if qId in qid_set:
                    qid_duplicates.append({
                        'row': row_num,
                        'qId': qId,
                        'field': 'qId',
                        'issue': 'qIdが重複',
                        'severity': 'ERROR',
                        'recommendation': 'qIdをユニークにしてください'
                    })
                else:
                    qid_set.add(qId)

                # セグメント統計
                segmentId = row.get('segmentId', '').strip()
                if segmentId:
                    segment_stats[segmentId] += 1

            # 選択肢タイプ統計
            has_e = row.get('choiceE', '').strip() != ''
            if has_e:
                choice_type_stats['5択'] += 1
            else:
                choice_type_stats['4択'] += 1

            # 各検証の実行
            all_errors.extend(validate_required_fields(row, row_num))
            all_errors.extend(validate_choice_consistency(row, row_num))
            all_errors.extend(validate_qid_format(row, row_num))
            all_errors.extend(validate_segment_consistency(row, row_num))
            all_errors.extend(validate_source_ref_format(row, row_num))
            all_errors.extend(validate_text_quality(row, row_num))
            all_errors.extend(validate_metadata_fields(row, row_num))

    # 重複エラーを追加
    all_errors.extend(qid_duplicates)

    # 統計情報表示
    print(f"総データ数: {row_count}問")
    print(f"ユニークqId数: {len(qid_set)}")
    print(f"重複qId数: {len(qid_duplicates)}")
    print()

    print("セグメント別問題数:")
    for segment, count in sorted(segment_stats.items()):
        print(f"  {segment}: {count}問")
    print()

    print("選択肢タイプ別:")
    for choice_type, count in sorted(choice_type_stats.items()):
        print(f"  {choice_type}: {count}問")
    print()

    # エラー集計
    error_count = sum(1 for e in all_errors if e['severity'] == 'ERROR')
    warning_count = sum(1 for e in all_errors if e['severity'] == 'WARNING')
    info_count = sum(1 for e in all_errors if e['severity'] == 'INFO')

    print(f"検出された問題:")
    print(f"  ERROR: {error_count}件")
    print(f"  WARNING: {warning_count}件")
    print(f"  INFO: {info_count}件")
    print(f"  合計: {len(all_errors)}件")
    print()

    # エラーレポート出力
    if all_errors:
        with open(report_file, 'w', encoding='utf-8', newline='') as f:
            fieldnames = ['row', 'qId', 'field', 'issue', 'severity', 'recommendation']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            # 重要度順にソート（ERROR → WARNING → INFO）
            severity_order = {'ERROR': 0, 'WARNING': 1, 'INFO': 2}
            sorted_errors = sorted(all_errors,
                                   key=lambda x: (severity_order.get(x['severity'], 3), x['row']))

            for error in sorted_errors:
                writer.writerow(error)

        print(f"レポート出力: {report_file}")

        # 上位10件のエラーを表示
        print()
        print("主要な問題（上位10件）:")
        print("-" * 80)
        for i, error in enumerate(sorted_errors[:10], 1):
            print(f"{i}. 行{error['row']} [{error['severity']}] {error['qId']}")
            print(f"   フィールド: {error['field']}")
            print(f"   問題: {error['issue']}")
            print(f"   推奨: {error['recommendation']}")
            print()
    else:
        print("✓ エラーは検出されませんでした")

    print("-" * 80)
    print("検証完了")

    return 0 if error_count == 0 else 1

if __name__ == '__main__':
    sys.exit(main())
