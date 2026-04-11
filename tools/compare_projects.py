# coding: utf-8
"""
プロジェクト1（doboku-14w-training）とプロジェクト2（eラーニングサイト）の比較・統合
"""
import sys
import csv
import re
from pathlib import Path
from docx import Document

sys.stdout.reconfigure(encoding='utf-8')

def load_project1_csv(csv_path):
    """プロジェクト1のCSVを読み込み、解説文の有無を確認"""
    questions = {}

    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            qid = row.get('qId', '')
            if not qid:
                continue

            # 解説文フィールドをチェック
            has_explain_short = bool(row.get('explainShort', '').strip())
            has_explain_a = bool(row.get('explainA', '').strip())
            has_explain_b = bool(row.get('explainB', '').strip())
            has_explain_c = bool(row.get('explainC', '').strip())
            has_explain_d = bool(row.get('explainD', '').strip())

            questions[qid] = {
                'qId': qid,
                'segmentId': row.get('segmentId', ''),
                'stem': row.get('stem', '')[:50],
                'has_explain_short': has_explain_short,
                'has_explain_a': has_explain_a,
                'has_explain_b': has_explain_b,
                'has_explain_c': has_explain_c,
                'has_explain_d': has_explain_d,
                'complete': has_explain_short and has_explain_a and has_explain_b and has_explain_c and has_explain_d
            }

    return questions

def extract_explanations_from_project2():
    """プロジェクト2のdocxファイルから解説文を抽出"""
    base_dir = Path(r"C:\Users\masam\Desktop\KeyenceRK\１級土木施工管理技術検定愛一時検定_eラーニングサイト\１級土木")

    explanations = {}

    docx_files = [f for f in sorted(base_dir.glob("*.docx"))
                  if "(1)" not in f.name and "(2)" not in f.name]

    for docx_file in docx_files:
        # ファイル名から年度を抽出
        match = re.search(r'令和(\d+|元)年度', docx_file.name)
        if not match:
            continue

        year = match.group(1)
        if year == "元":
            year_prefix = "R1gakka"
        else:
            year_prefix = f"R{year}gakka"

        print(f"読み込み中: {docx_file.name}")

        try:
            doc = Document(docx_file)

            # 問題番号ごとに解説文を抽出
            current_q = None
            current_text = []

            for para in doc.paragraphs:
                text = para.text.strip()

                # 問題番号を検出
                patterns = [
                    r'^No\.?\s*(\d+)',
                    r'^問\s*(\d+)',
                    r'^第?\s*(\d+)\s*問',
                    r'^(\d+)[\.\)]\s',
                ]

                matched = False
                for pattern in patterns:
                    m = re.match(pattern, text, re.IGNORECASE)
                    if m:
                        # 前の問題の解説を保存
                        if current_q and current_text:
                            explanation = '\n'.join(current_text)
                            explanations[current_q] = explanation

                        # 新しい問題番号
                        q_num = int(m.group(1))
                        # qIdを生成（例: R6gakkaA-001）
                        # ただし、A/Bの区別がわからないので、両方試す必要がある
                        current_q = f"{year_prefix}A-{q_num:03d}"
                        current_text = [text]
                        matched = True
                        break

                if not matched and current_q:
                    # 問題番号以降の内容を蓄積
                    if text:
                        current_text.append(text)

            # 最後の問題の解説を保存
            if current_q and current_text:
                explanation = '\n'.join(current_text)
                explanations[current_q] = explanation

        except Exception as e:
            print(f"  エラー: {e}")

    return explanations

def main():
    print("="*80)
    print("プロジェクト1とプロジェクト2の比較")
    print("="*80)

    # プロジェクト1のCSVを読み込み
    project1_csv = Path(r"C:\ProgramData\Generative AI\Github\doboku-14w-training\tools\questionbank_drive_import.csv")

    if not project1_csv.exists():
        print(f"エラー: プロジェクト1のCSVが見つかりません: {project1_csv}")
        return

    print(f"\n📊 プロジェクト1のCSVを分析中...")
    p1_questions = load_project1_csv(project1_csv)

    print(f"  総問題数: {len(p1_questions)}")

    # 解説文の完全性を集計
    complete = [q for q in p1_questions.values() if q['complete']]
    incomplete = [q for q in p1_questions.values() if not q['complete']]

    print(f"  完全な解説あり: {len(complete)}問 ({len(complete)/len(p1_questions)*100:.1f}%)")
    print(f"  不完全/なし: {len(incomplete)}問 ({len(incomplete)/len(p1_questions)*100:.1f}%)")

    # 年度別に不足を確認
    print(f"\n📋 年度別の不足状況:")
    for year in ['R1', 'R2', 'R3', 'R4', 'R5', 'R6', 'R7']:
        year_incomplete = [q for q in incomplete if q['qId'].startswith(year)]
        if year_incomplete:
            print(f"  {year}: {len(year_incomplete)}問不足")
            # サンプル表示
            sample = year_incomplete[:5]
            for q in sample:
                print(f"    - {q['qId']}: {q['stem']}")

    # プロジェクト2の解説文を抽出
    print(f"\n📄 プロジェクト2のdocxファイルから解説文を抽出中...")
    p2_explanations = extract_explanations_from_project2()

    print(f"  抽出された解説数: {len(p2_explanations)}")

    # プロジェクト1に不足していて、プロジェクト2にある解説を特定
    print(f"\n🔍 プロジェクト2から流用可能な解説:")
    usable = []

    for q in incomplete:
        qid = q['qId']
        # A/B両方チェック
        for gakka in ['A', 'B']:
            test_qid = qid.replace('gakka', f'gakka{gakka}')
            if test_qid in p2_explanations:
                usable.append({
                    'qId': qid,
                    'source_qId': test_qid,
                    'explanation': p2_explanations[test_qid][:100]  # サンプル
                })
                break

    print(f"  流用可能: {len(usable)}問")

    if usable:
        print(f"\n  サンプル:")
        for item in usable[:10]:
            print(f"    {item['qId']} ← {item['source_qId']}: {item['explanation'][:50]}...")

    # サマリー
    print(f"\n\n" + "="*80)
    print("【サマリー】")
    print("="*80)
    print(f"プロジェクト1 不足: {len(incomplete)}問")
    print(f"プロジェクト2 解説数: {len(p2_explanations)}問")
    print(f"流用可能: {len(usable)}問")
    print(f"残り手作業必要: {len(incomplete) - len(usable)}問")

if __name__ == "__main__":
    main()
