# coding: utf-8
"""
最後の3問の解説をCSVに統合
"""
import sys
import csv
from pathlib import Path
from datetime import datetime
from docx import Document
import re

sys.stdout.reconfigure(encoding='utf-8')

def extract_explanations_from_docx(docx_path):
    """docxから3問の解説を抽出"""
    doc = Document(docx_path)
    
    explanations = {}
    current_qid = None
    current_section = None
    current_data = {}
    
    for para in doc.paragraphs:
        text = para.text.strip()
        
        # qIdを検出
        qid_match = re.match(r'(R\d+gakkaA-\d+)', text)
        if qid_match:
            # 前の問題を保存
            if current_qid and current_data:
                explanations[current_qid] = current_data
            
            current_qid = qid_match.group(1)
            current_data = {
                'explainA': '',
                'explainB': '',
                'explainC': '',
                'explainD': '',
                'explainShort': ''
            }
            continue
        
        # 選択肢解説を抽出
        choice_match = re.match(r'^([A-D])\.\s*(.+?)→\s*(.+)$', text)
        if choice_match and current_qid:
            choice = choice_match.group(1)
            explanation = choice_match.group(3).strip()
            current_data[f'explain{choice}'] = explanation
            continue
        
        # 全体解説を抽出
        if text.startswith('全体解説:') and current_qid:
            explain_short = text.replace('全体解説:', '').strip()
            current_data['explainShort'] = explain_short
    
    # 最後の問題を保存
    if current_qid and current_data:
        explanations[current_qid] = current_data
    
    return explanations

def update_csv(csv_path, explanations):
    """CSVを更新"""
    
    # CSVを読み込み
    rows = []
    fieldnames = []
    
    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for row in reader:
            rows.append(row)
    
    # 更新統計
    updated = []
    
    # 各行を更新
    for row in rows:
        qid = row['qId']
        if qid in explanations:
            exp = explanations[qid]
            
            # 解説を更新
            row['explainA'] = exp['explainA']
            row['explainB'] = exp['explainB']
            row['explainC'] = exp['explainC']
            row['explainD'] = exp['explainD']
            row['explainShort'] = exp['explainShort']
            
            updated.append(qid)
    
    # バックアップ
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = csv_path.parent / f"questionbank_drive_import_backup_{timestamp}.csv"
    
    print(f"バックアップ作成: {backup_path.name}")
    with open(backup_path, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        with open(csv_path, 'r', encoding='utf-8-sig') as orig:
            reader = csv.DictReader(orig)
            for row in reader:
                writer.writerow(row)
    
    # 更新後のCSVを書き込み
    print(f"CSV更新: {csv_path.name}")
    with open(csv_path, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    
    return updated

def main():
    print("="*80)
    print("最後の3問の解説をCSVに統合")
    print("="*80)
    
    # docxパス
    docx_path = Path(r"C:\Users\masam\Desktop\新規 Microsoft Word 文書.docx")
    
    if not docx_path.exists():
        print(f"エラー: docxファイルが見つかりません: {docx_path}")
        return
    
    # 解説を抽出
    print(f"\ndocxから解説を抽出中...")
    explanations = extract_explanations_from_docx(docx_path)
    
    print(f"抽出完了: {len(explanations)}問")
    for qid in explanations:
        print(f"  - {qid}")
    
    # CSVを更新
    csv_path = Path(r"C:\ProgramData\Generative AI\Github\doboku-14w-training\tools\questionbank_drive_import.csv")
    
    print(f"\nCSVを更新中...")
    updated = update_csv(csv_path, explanations)
    
    print(f"\n\n" + "="*80)
    print("【統合結果】")
    print("="*80)
    print(f"更新した問題: {len(updated)}問")
    for qid in updated:
        print(f"  ✓ {qid}")
    
    print(f"\n✅ 統合完了！")
    print(f"更新されたCSV: {csv_path}")

if __name__ == "__main__":
    main()
