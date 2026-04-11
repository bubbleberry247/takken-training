#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
DOCXファイルから穴埋め問題を抽出してCSVに反映するスクリプト
"""
import csv
import sys
import re
import docx
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

DOCX_DIR = Path(r"C:\Users\masam\Desktop\KeyenceRK\１級土木施工管理技術検定愛一時検定_eラーニングサイト\docx_out")
CSV_PATH = Path(r"C:\ProgramData\Generative AI\Github\doboku-14w-training\tools\questionbank_drive_import.csv")

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

def parse_qid(qid):
    """qIdから年度、gakka、問題番号を抽出"""
    match = re.match(r'(R\d+)(gakka[AB])-(\d+)', qid)
    if match:
        year, gakka, num = match.groups()
        return year, gakka, int(num)
    return None, None, None

def extract_question_from_docx(docx_path, question_num):
    """DOCXファイルから指定された問題番号のテキストを抽出"""
    try:
        doc = docx.Document(docx_path)

        # 問題を探す
        found = False
        question_lines = []

        for para in doc.paragraphs:
            text = para.text.strip()

            # 問題番号を見つけた
            if f'【No. {question_num}】' in text or f'【No.{question_num}】' in text:
                found = True
                question_lines.append(text)
                continue

            # 問題が見つかった後、次の問題まで収集
            if found:
                if '【No.' in text and text != question_lines[0]:
                    break
                if text:
                    question_lines.append(text)

        if question_lines:
            # テキストを結合
            full_text = '\n'.join(question_lines)

            # 問題番号行を削除
            full_text = re.sub(r'【No\.\s*\d+】\s*', '', full_text)

            # 穴埋めマーカーを（イ）（ロ）（ハ）（ニ）に統一変換

            # まず導入文のマーカー表記を修正
            # 「ののQ〜R」「ののR〜S」「ののS〜T」などを「の(イ)〜(ニ)」に統一
            full_text = re.sub(r'のの[A-Z]〜[A-Z]に', 'の(イ)〜(ニ)に', full_text)

            # 本文中のアルファベットマーカーを検出して順番に置換
            # 使用されているアルファベット（スペースで囲まれた1文字）を抽出
            markers = re.findall(r'\s([A-Z])\s', full_text)
            unique_markers = []
            for m in markers:
                if m not in unique_markers:
                    unique_markers.append(m)

            # 最大4つのマーカーを(イ)、(ロ)、(ハ)、(ニ)に変換
            marker_map = {
                0: '(イ)',
                1: '(ロ)',
                2: '(ハ)',
                3: '(ニ)'
            }

            # 本文中のすべてのマーカーを置換
            # 単語境界パターンを使用してより広範囲に置換
            for i, marker in enumerate(unique_markers[:4]):
                # 単語境界で囲まれたマーカーを置換
                full_text = re.sub(rf'\b{marker}\b', marker_map[i], full_text)

            # 念のため「のの(」→「の(」
            full_text = full_text.replace('のの(', 'の(')

            # 先頭の導入文を抽出
            intro_match = re.match(r'^(.+?に関する下記の文章中の.+?どれか\.)', full_text, re.DOTALL)
            if intro_match:
                intro = intro_match.group(1)
                # 導入文を整形
                intro = intro.replace('\n', '')

                # 残りの本文を整形
                body = full_text[len(intro):].strip()

                # 導入文 + 改行 + 本文
                return intro + '\n\n' + body

            return full_text.strip()

        return None
    except Exception as e:
        print(f"エラー: {docx_path} - {e}")
        return None

# CSVを読み込み
with open(CSV_PATH, 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    rows = list(reader)
    fieldnames = reader.fieldnames

updated_count = 0
failed_count = 0

# 各qIdに対してDOCXから抽出
for qid in fill_in_qids:
    year, gakka, num = parse_qid(qid)
    if not year or not gakka:
        print(f"✗ {qid}: qIdのパースに失敗")
        failed_count += 1
        continue

    # DOCXファイルパスを取得
    docx_filename = f"{year}{gakka}_mondai.docx"
    docx_path = DOCX_DIR / docx_filename

    if not docx_path.exists():
        print(f"✗ {qid}: DOCXファイルが見つかりません（{docx_filename}）")
        failed_count += 1
        continue

    # テキストを抽出
    extracted_text = extract_question_from_docx(docx_path, num)

    if not extracted_text:
        print(f"✗ {qid}: DOCXからテキストを抽出できませんでした")
        failed_count += 1
        continue

    # CSVの該当行を更新
    for row in rows:
        if row['qId'] == qid:
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
print(f"合計: {len(fill_in_qids)}件")
