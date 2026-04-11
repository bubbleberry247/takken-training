#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
不足説明文.docxからexplainA-Dを抽出し、questionbank_drive_import.csvに統合する

使用方法:
    python merge_explanations_from_docx.py

機能:
    1. 不足説明文.docxからMarkdownテーブルを抽出
    2. questionbank_drive_import.csvの該当行を更新（explainA-Dフィールド）
    3. バックアップを自動作成
    4. 統合結果レポートを出力
"""

import sys
import io
import csv
from datetime import datetime
from pathlib import Path
from docx import Document

# UTF-8出力設定
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# ファイルパス
DOCX_PATH = Path(r"C:\Users\masam\Downloads\不足説明文.docx")
CSV_PATH = Path(r"C:\ProgramData\Generative AI\Github\doboku-14w-training\tools\questionbank_drive_import.csv")
BACKUP_DIR = CSV_PATH.parent

def extract_table_from_docx(docx_path):
    """
    Wordドキュメントから収集データテーブルを抽出

    Returns:
        dict: {qId: {explainA, explainB, explainC, explainD, ...}}
    """
    doc = Document(docx_path)

    # テーブル開始行を探す（'| qId |' で始まる行）
    table_started = False
    data_lines = []

    for i, para in enumerate(doc.paragraphs):
        text = para.text.strip()

        # ヘッダー行を検出
        if text.startswith('| qId |'):
            table_started = True
            continue

        # セパレータ行をスキップ（'|-----|'）
        if table_started and text.startswith('|--'):
            continue

        # データ行を収集
        if table_started and text.startswith('|') and not text.startswith('| qId'):
            # テーブル終了判定（Rで始まるqIdを含む行を収集）
            # R1〜R7年度全てに対応
            import re
            if re.search(r'R[0-9]gakka[AB]', text):
                data_lines.append(text)
            elif text.strip() == '':
                # 空行でテーブル終了
                break

    if not data_lines:
        raise ValueError("データ行が見つかりません")

    print(f"データ行数: {len(data_lines)}")

    # データをパース（固定列数: 9列）
    # 形式: | qId | explainA | explainB | explainC | explainD | explainShort | explainLong | 状態 | ID |
    explanations = {}

    for line_num, line in enumerate(data_lines, 1):
        # 先頭と末尾の | を除去
        line = line.strip()
        if line.startswith('|'):
            line = line[1:]
        if line.endswith('|'):
            line = line[:-1]

        # パイプで分割（最大8回まで - 9列）
        cells = line.split('|', 8)

        if len(cells) < 9:
            print(f"警告: 行{line_num}は列数不足 ({len(cells)}/9): {line[:80]}...")
            continue

        # セルをトリム
        cells = [c.strip() for c in cells]

        qid = cells[0]
        explain_a = cells[1]
        explain_b = cells[2]
        explain_c = cells[3]
        explain_d = cells[4]
        explain_short = cells[5]
        explain_long = cells[6]
        status = cells[7]
        item_id = cells[8]

        # qIdの検証（R1〜R7年度全てに対応）
        import re
        if not re.match(r'^R[1-7]gakka[AB]-\d+', qid):
            print(f"警告: 行{line_num}は無効なqId: {qid}")
            continue

        explanations[qid] = {
            'explainA': explain_a,
            'explainB': explain_b,
            'explainC': explain_c,
            'explainD': explain_d,
            'explainShort': explain_short,
            'status': status,
        }

        print(f"✓ {qid}: explainA={explain_a[:30]}...")

    return explanations


def merge_explanations_to_csv(explanations, csv_path):
    """
    CSVファイルのexplainA-Dフィールドを更新

    Args:
        explanations: {qId: {explainA, explainB, explainC, explainD}}
        csv_path: CSVファイルパス

    Returns:
        dict: 統計情報
    """
    # バックアップ作成
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = csv_path.parent / f"{csv_path.stem}_backup_{timestamp}{csv_path.suffix}"

    import shutil
    shutil.copy2(csv_path, backup_path)
    print(f"✓ バックアップ作成: {backup_path.name}")

    # CSVを読み込み
    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    # 統計
    stats = {
        'total': len(rows),
        'updated': 0,
        'skipped': 0,
        'not_found': 0,
    }

    # explainA-Dを更新
    for row in rows:
        qid = row.get('qId', '')

        if qid in explanations:
            exp = explanations[qid]

            # 既存の説明文があるかチェック
            has_existing = any([
                row.get('explainA', '').strip(),
                row.get('explainB', '').strip(),
                row.get('explainC', '').strip(),
                row.get('explainD', '').strip(),
            ])

            if has_existing:
                print(f"⚠️  {qid}: 既存の説明文あり - 上書き")

            # 更新
            row['explainA'] = exp['explainA']
            row['explainB'] = exp['explainB']
            row['explainC'] = exp['explainC']
            row['explainD'] = exp['explainD']

            # explainShortも更新（より詳細な説明がある場合）
            if exp.get('explainShort') and exp['explainShort'] != row.get('explainShort', ''):
                print(f"  → explainShortも更新: {exp['explainShort'][:50]}...")
                row['explainShort'] = exp['explainShort']

            stats['updated'] += 1
        else:
            stats['skipped'] += 1

    # 見つからなかったqIdを記録
    for qid in explanations:
        if qid not in [row.get('qId', '') for row in rows]:
            print(f"❌ {qid}: CSVに存在しません")
            stats['not_found'] += 1

    # CSVに書き戻し
    with open(csv_path, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\n✓ CSV更新完了: {csv_path.name}")

    return stats


def main():
    print("=== 不足説明文.docx → CSV統合スクリプト ===\n")

    # 1. Wordドキュメントから抽出
    print(f"[1/3] Wordドキュメントを読み込み: {DOCX_PATH.name}")
    try:
        explanations = extract_table_from_docx(DOCX_PATH)
        print(f"✓ 抽出完了: {len(explanations)}問\n")
    except Exception as e:
        print(f"❌ エラー: {e}")
        return 1

    # 2. サマリー表示
    print(f"[2/3] 抽出データサマリー:")
    print(f"  - 総問題数: {len(explanations)}問")
    print(f"  - qId範囲: {min(explanations.keys())} 〜 {max(explanations.keys())}")
    print(f"  - 完了状態: {sum(1 for e in explanations.values() if e['status'] == '✅完了')}問")
    print()

    # 3. CSVに統合
    print(f"[3/3] CSVに統合: {CSV_PATH.name}")
    stats = merge_explanations_to_csv(explanations, CSV_PATH)

    # 結果レポート
    print("\n" + "="*80)
    print("統合結果レポート")
    print("="*80)
    print(f"CSV総問題数:     {stats['total']}問")
    print(f"更新された問題:   {stats['updated']}問 ✅")
    print(f"スキップ:        {stats['skipped']}問（説明文収集対象外）")
    print(f"CSV未登録:       {stats['not_found']}問 ❌")
    print("="*80)

    if stats['updated'] > 0:
        print("\n✅ 統合完了！次のステップ:")
        print("   1. CSVをGoogle Sheetsにインポート")
        print("   2. Webアプリで表示を確認")
        print(f"   3. 残り{155 - stats['updated']}問の収集を継続（任意）")

    return 0


if __name__ == '__main__':
    sys.exit(main())
