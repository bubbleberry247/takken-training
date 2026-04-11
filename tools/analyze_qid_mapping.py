# coding: utf-8
"""
qIdのマッピング調査
プロジェクト1とプロジェクト2のqId命名規則を理解する
"""
import sys
import csv
import re
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

def analyze_project1_qids(csv_path):
    """プロジェクト1のqId形式を分析"""
    qids = []

    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            qid = row.get('qId', '')
            segment_id = row.get('segmentId', '')
            if qid:
                qids.append({
                    'qId': qid,
                    'segmentId': segment_id
                })

    return qids

def analyze_docx_question_format():
    """プロジェクト2のdocxファイルの問題番号形式を分析"""
    from docx import Document

    base_dir = Path(r"C:\Users\masam\Desktop\KeyenceRK\１級土木施工管理技術検定愛一時検定_eラーニングサイト\１級土木")

    # R6の解説文を詳しく見る
    r6_docx = base_dir / "1級土木 解説文集 令和6年度.docx"

    if not r6_docx.exists():
        print(f"ファイルが見つかりません: {r6_docx}")
        return

    doc = Document(r6_docx)

    print("="*80)
    print("R6解説文集の構造分析")
    print("="*80)

    question_starts = []
    for i, para in enumerate(doc.paragraphs[:100]):  # 最初の100段落
        text = para.text.strip()
        if not text:
            continue

        # 問題番号っぽいパターンを検出
        patterns = [
            r'^No\.?\s*(\d+)',
            r'^問\s*(\d+)',
            r'^第?\s*(\d+)\s*問',
            r'^(\d+)[\.\)]\s',
            r'令和\d+年.*[AB].*第?(\d+)問',
        ]

        for pattern in patterns:
            m = re.match(pattern, text, re.IGNORECASE)
            if m:
                question_starts.append({
                    'line': i + 1,
                    'number': m.group(1),
                    'text': text[:80]
                })
                break

    print(f"\n検出された問題番号の開始位置（最初の20個）:")
    for item in question_starts[:20]:
        print(f"  行{item['line']:3d}: 問{item['number']:>3s} - {item['text']}")

def main():
    # プロジェクト1のqIdサンプル
    project1_csv = Path(r"C:\ProgramData\Generative AI\Github\doboku-14w-training\tools\questionbank_drive_import.csv")

    print("="*80)
    print("プロジェクト1のqId形式分析")
    print("="*80)

    qids = analyze_project1_qids(project1_csv)

    # R6のqIdサンプルを表示
    r6_qids = [q for q in qids if q['qId'].startswith('R6')]

    print(f"\nR6のqIdサンプル（最初の20個）:")
    for q in r6_qids[:20]:
        print(f"  {q['qId']:<20} (segment: {q['segmentId']})")

    print(f"\nR6の総問題数: {len(r6_qids)}")

    # 学科A/Bの分布
    r6_a = [q for q in r6_qids if 'gakkaA' in q['qId']]
    r6_b = [q for q in r6_qids if 'gakkaB' in q['qId']]

    print(f"  学科A: {len(r6_a)}問")
    print(f"  学科B: {len(r6_b)}問")

    # R6のqIdパターンを確認
    print(f"\nR6学科Aのqid範囲:")
    if r6_a:
        print(f"  最小: {r6_a[0]['qId']}")
        print(f"  最大: {r6_a[-1]['qId']}")

    print(f"\nR6学科Bのqid範囲:")
    if r6_b:
        print(f"  最小: {r6_b[0]['qId']}")
        print(f"  最大: {r6_b[-1]['qId']}")

    # プロジェクト2の分析
    print(f"\n\n")
    analyze_docx_question_format()

if __name__ == "__main__":
    main()
