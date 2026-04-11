# coding: utf-8
"""
統合後のCSVを検証
"""
import sys
import csv
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

def verify_csv(csv_path):
    """CSVの解説文カバレッジを検証"""

    questions = []

    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            qid = row['qId']
            has_explain_short = bool(row.get('explainShort', '').strip())
            has_explain_a = bool(row.get('explainA', '').strip())
            has_explain_b = bool(row.get('explainB', '').strip())
            has_explain_c = bool(row.get('explainC', '').strip())
            has_explain_d = bool(row.get('explainD', '').strip())

            questions.append({
                'qId': qid,
                'has_explain_short': has_explain_short,
                'has_all_choices': has_explain_a and has_explain_b and has_explain_c and has_explain_d,
                'complete': has_explain_short and has_explain_a and has_explain_b and has_explain_c and has_explain_d
            })

    return questions

def main():
    csv_path = Path(r"C:\ProgramData\Generative AI\Github\doboku-14w-training\tools\questionbank_drive_import.csv")

    print("="*80)
    print("統合後のCSV検証")
    print("="*80)

    questions = verify_csv(csv_path)

    print(f"\n総問題数: {len(questions)}")

    # explainShortの統計
    with_explain_short = [q for q in questions if q['has_explain_short']]
    without_explain_short = [q for q in questions if not q['has_explain_short']]

    print(f"\nexplainShort:")
    print(f"  あり: {len(with_explain_short)}問 ({len(with_explain_short)/len(questions)*100:.1f}%)")
    print(f"  なし: {len(without_explain_short)}問 ({len(without_explain_short)/len(questions)*100:.1f}%)")

    # 選択肢解説の統計
    with_all_choices = [q for q in questions if q['has_all_choices']]
    without_all_choices = [q for q in questions if not q['has_all_choices']]

    print(f"\n選択肢解説（A-D全て）:")
    print(f"  あり: {len(with_all_choices)}問 ({len(with_all_choices)/len(questions)*100:.1f}%)")
    print(f"  不完全: {len(without_all_choices)}問 ({len(without_all_choices)/len(questions)*100:.1f}%)")

    # 完全な解説
    complete = [q for q in questions if q['complete']]
    incomplete = [q for q in questions if not q['complete']]

    print(f"\n完全な解説（explainShort + 選択肢A-D）:")
    print(f"  完全: {len(complete)}問 ({len(complete)/len(questions)*100:.1f}%)")
    print(f"  不完全: {len(incomplete)}問 ({len(incomplete)/len(questions)*100:.1f}%)")

    # 不完全な問題の詳細
    if incomplete:
        print(f"\n不完全な問題の内訳:")

        # explainShortのみ不足
        only_short_missing = [q for q in incomplete if not q['has_explain_short'] and q['has_all_choices']]
        print(f"  explainShortのみ不足: {len(only_short_missing)}問")

        # 選択肢解説のみ不足
        only_choices_missing = [q for q in incomplete if q['has_explain_short'] and not q['has_all_choices']]
        print(f"  選択肢解説のみ不足: {len(only_choices_missing)}問")

        # 両方不足
        both_missing = [q for q in incomplete if not q['has_explain_short'] and not q['has_all_choices']]
        print(f"  両方不足: {len(both_missing)}問")

    # 年度別統計
    print(f"\n年度別統計（explainShort基準）:")
    for year in ['R1', 'R2', 'R3', 'R4', 'R5', 'R6', 'R7']:
        year_questions = [q for q in questions if q['qId'].startswith(year)]
        year_with_short = [q for q in year_questions if q['has_explain_short']]

        if year_questions:
            coverage = len(year_with_short) / len(year_questions) * 100
            print(f"  {year}: {len(year_with_short)}/{len(year_questions)}問 ({coverage:.1f}%)")

    # 不足している問題のリスト
    if without_explain_short:
        print(f"\n\nexplainShortが不足している問題（全{len(without_explain_short)}問）:")
        for q in without_explain_short[:50]:  # 最初の50問まで表示
            print(f"  {q['qId']}")

        if len(without_explain_short) > 50:
            print(f"  ... 他{len(without_explain_short) - 50}問")

    print(f"\n\n" + "="*80)
    print("【結論】")
    print("="*80)
    print(f"プロジェクト2から {len(with_explain_short) - 527}問の解説を追加")
    print(f"現在のカバレッジ: {len(with_explain_short)}/{len(questions)}問 ({len(with_explain_short)/len(questions)*100:.1f}%)")
    print(f"残り不足: {len(without_explain_short)}問")

if __name__ == "__main__":
    main()
