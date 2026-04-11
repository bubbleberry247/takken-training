#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
穴埋め問題の本文をPDFから抽出してCSVに追加するスクリプト
"""
import csv
import sys
import re
import PyPDF2
from pathlib import Path

# 標準出力のエンコーディングをUTF-8に設定
sys.stdout.reconfigure(encoding='utf-8')

# PDFディレクトリとCSVファイルのパス
PDF_DIR = Path(r"C:\Users\masam\Desktop\KeyenceRK\１級土木施工管理技術検定愛一時検定_eラーニングサイト")
CSV_PATH = Path(r"C:\ProgramData\Generative AI\Github\doboku-14w-training\tools\questionbank_drive_import.csv")

# 穴埋めマーカーが欠けている問題のqIdリスト（穴埋め問題のみ、図表問題は除外）
MISSING_MARKERS_QIDS = [
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


def parse_qid(qid):
    """qIdから年度、gakka、問題番号を抽出"""
    match = re.match(r'(R\d+)(gakka[AB])-(\d+)', qid)
    if match:
        year, gakka, num = match.groups()
        return year, gakka, int(num)
    return None, None, None


def find_pdf_file(year, gakka):
    """PDFファイルのパスを取得"""
    pdf_name = f"{year}{gakka}_mondai.pdf"
    pdf_path = PDF_DIR / pdf_name
    if pdf_path.exists():
        return pdf_path
    return None


def extract_question_text_from_pdf(pdf_path, question_num):
    """PDFから指定された問題番号のテキストを抽出"""
    try:
        with open(pdf_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            total_pages = len(reader.pages)

            # 問題番号からページ範囲を推定（午前：1-66、午後：1-35）
            # 1ページあたり約2問と仮定
            estimated_page = (question_num - 1) // 2

            # 前後3ページを探索
            start_page = max(0, estimated_page - 3)
            end_page = min(total_pages, estimated_page + 4)

            for page_num in range(start_page, end_page):
                page = reader.pages[page_num]
                text = page.extract_text()

                # 問題番号のパターンを探す
                patterns = [
                    f'No. {question_num}】',
                    f'No.{question_num}】',
                    f'【No. {question_num}',
                    f'【No.{question_num}'
                ]

                for pattern in patterns:
                    if pattern in text:
                        # 問題テキストを抽出（次の問題番号の前まで）
                        start_idx = text.find(pattern)

                        # 次の問題を探す
                        next_question_patterns = [
                            f'【No. {question_num + 1}】',
                            f'【No.{question_num + 1}】'
                        ]

                        end_idx = len(text)
                        for next_pattern in next_question_patterns:
                            next_idx = text.find(next_pattern, start_idx + 1)
                            if next_idx != -1:
                                end_idx = next_idx
                                break

                        question_text = text[start_idx:end_idx]
                        return clean_question_text(question_text)

            return None
    except Exception as e:
        print(f"PDFエラー: {pdf_path} - {e}")
        return None


def clean_question_text(text):
    """抽出されたテキストをクリーンアップ"""
    # 問題番号の行を削除
    lines = text.split('\n')
    cleaned_lines = []

    for line in lines:
        # 問題番号の行をスキップ
        if re.match(r'.*【No\.\s*\d+】.*', line):
            continue
        # ページ番号などの不要な行をスキップ
        if re.match(r'^\s*[―\-]+\s*\d+\s*[―\-]+\s*$', line):
            continue
        if re.match(r'^DHP-[AB]\.smd.*', line):
            continue

        cleaned_lines.append(line)

    text = '\n'.join(cleaned_lines).strip()

    # 文字化け記号を（イ）（ロ）（ハ）（ニ）に置換
    # べc2ゃさぱ → （イ）
    # べc2ゃざざ → （ロ）
    # べc2ゃゃゃ → （ハ）
    # べc2ゃゃ3 → （ニ）

    replacements = {
        'べc2ゃさぱ': '（イ）',
        'べc2ゃざざ': '（ロ）',
        'べc2ゃゃゃ': '（ハ）',
        'べc2ゃゃ3': '（ニ）',
        # 年数の置換
        'べc2はみふ年': '1年',
        'べc2はみ3年': '3年',
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    return text


def update_csv_with_extracted_text():
    """CSVを読み込み、抽出されたテキストでstemを更新"""
    # CSVを読み込み
    with open(CSV_PATH, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fieldnames = reader.fieldnames

    updated_count = 0
    failed_count = 0

    for qid in MISSING_MARKERS_QIDS:
        # R3gakkaB-031は既に更新済みなのでスキップ
        if qid == 'R3gakkaB-031':
            print(f"✓ {qid}: 既に更新済み（スキップ）")
            continue

        year, gakka, num = parse_qid(qid)
        if not year or not gakka:
            print(f"✗ {qid}: qIdのパースに失敗")
            failed_count += 1
            continue

        # PDFファイルを取得
        pdf_path = find_pdf_file(year, gakka)
        if not pdf_path:
            print(f"✗ {qid}: PDFファイルが見つかりません（{year}{gakka}_mondai.pdf）")
            failed_count += 1
            continue

        # テキストを抽出
        extracted_text = extract_question_text_from_pdf(pdf_path, num)
        if not extracted_text:
            print(f"✗ {qid}: PDFからテキストを抽出できませんでした")
            failed_count += 1
            continue

        # CSVの該当行を更新
        for row in rows:
            if row['qId'] == qid:
                old_stem = row['stem']

                # 既存のstemに抽出されたテキストを追加
                # （既存のstemには問題の導入部分が含まれている場合がある）
                if old_stem and len(old_stem) > 20:
                    # 既存のstemが長い場合は、抽出されたテキストを追加
                    # ただし、抽出されたテキストに既存のstemの一部が含まれているか確認
                    if old_stem[:50] in extracted_text:
                        # 抽出されたテキストに既存のstemが含まれている場合は置換
                        row['stem'] = extracted_text
                    else:
                        # 含まれていない場合は追加
                        row['stem'] = f"{old_stem}\n\n{extracted_text}"
                else:
                    # 既存のstemが短い場合は置換
                    row['stem'] = extracted_text

                print(f"✓ {qid}: stem更新完了（{len(extracted_text)}文字）")
                updated_count += 1
                break

    # CSVに書き戻し
    with open(CSV_PATH, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\n=== 処理完了 ===")
    print(f"更新成功: {updated_count}件")
    print(f"更新失敗: {failed_count}件")
    print(f"合計: {len(MISSING_MARKERS_QIDS)}件")


if __name__ == '__main__':
    update_csv_with_extracted_text()
