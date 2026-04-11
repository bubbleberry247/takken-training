#!/usr/bin/env python3
"""
R7gakkaA-039 OCR誤変換即座修正スクリプト

修正内容:
1. choiceA: `〜\日以上` → `4〜6日以上`
2. choiceC: `層,^m リフトの場合には\層` → `1層、1.5m リフトの場合には4層`
3. choiceD: `bmm` → `5mm`
"""

import csv
import sys
import io
from datetime import datetime
import shutil

# UTF-8標準出力
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def create_backup(csv_path):
    """バックアップ作成"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = csv_path.replace('.csv', f'_backup_{timestamp}.csv')
    shutil.copy2(csv_path, backup_path)
    print(f"✓ バックアップ作成: {backup_path}")
    return backup_path

def fix_r7gakkaa_039(csv_path):
    """R7gakkaA-039の誤変換を修正"""
    rows = []
    fixed = False

    # CSV読み込み
    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames

        for row in reader:
            if row['qId'] == 'R7gakkaA-039':
                print(f"\n{'='*80}")
                print(f"修正対象: {row['qId']}")
                print(f"{'='*80}")

                # choiceA修正
                original_a = row['choiceA']
                row['choiceA'] = row['choiceA'].replace('`〜\\日以上', '4〜6日以上')
                if original_a != row['choiceA']:
                    print(f"\n[choiceA修正]")
                    print(f"  修正前: {original_a[:100]}...")
                    print(f"  修正後: {row['choiceA'][:100]}...")

                # choiceC修正
                original_c = row['choiceC']
                # パターン1: `層,^m
                row['choiceC'] = row['choiceC'].replace('`層,^m', '1層、1.5m')
                # パターン2: \層
                row['choiceC'] = row['choiceC'].replace('\\層', '4層')
                if original_c != row['choiceC']:
                    print(f"\n[choiceC修正]")
                    print(f"  修正前: {original_c[:100]}...")
                    print(f"  修正後: {row['choiceC'][:100]}...")

                # choiceD修正
                original_d = row['choiceD']
                row['choiceD'] = row['choiceD'].replace('bmm', '5mm')
                if original_d != row['choiceD']:
                    print(f"\n[choiceD修正]")
                    print(f"  修正前: {original_d[:100]}...")
                    print(f"  修正後: {row['choiceD'][:100]}...")

                # explainA修正（choiceAの説明も同期）
                if '`〜' in row.get('explainA', '') or '\\日' in row.get('explainA', ''):
                    original_ea = row['explainA']
                    row['explainA'] = row['explainA'].replace('`〜', '3〜')
                    row['explainA'] = row['explainA'].replace('\\日', '4日')
                    if original_ea != row['explainA']:
                        print(f"\n[explainA修正]")
                        print(f"  修正前: {original_ea[:100]}...")
                        print(f"  修正後: {row['explainA'][:100]}...")

                # explainC修正（choiceCの説明も同期）
                if '`層' in row.get('explainC', '') or '\\層' in row.get('explainC', '') or '^m' in row.get('explainC', ''):
                    original_ec = row['explainC']
                    row['explainC'] = row['explainC'].replace('`層', '1層')
                    row['explainC'] = row['explainC'].replace('^m', '1.5m')
                    row['explainC'] = row['explainC'].replace('\\層', '4層')
                    if original_ec != row['explainC']:
                        print(f"\n[explainC修正]")
                        print(f"  修正前: {original_ec[:150]}...")
                        print(f"  修正後: {row['explainC'][:150]}...")

                # explainD修正（choiceDの説明も同期）
                if 'bmm' in row.get('explainD', ''):
                    original_ed = row['explainD']
                    row['explainD'] = row['explainD'].replace('bmm', '6mm')
                    if original_ed != row['explainD']:
                        print(f"\n[explainD修正]")
                        print(f"  修正前: {original_ed[:100]}...")
                        print(f"  修正後: {row['explainD'][:100]}...")

                fixed = True

            rows.append(row)

    if not fixed:
        print("⚠ 警告: R7gakkaA-039が見つかりませんでした")
        return False

    # CSV書き込み
    with open(csv_path, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\n{'='*80}")
    print(f"✓ 修正完了: {csv_path}")
    print(f"{'='*80}\n")
    return True

def main():
    csv_path = "C:/ProgramData/Generative AI/Github/doboku-14w-training/tools/questionbank_drive_import.csv"

    print(f"R7gakkaA-039 OCR誤変換修正開始...")
    print(f"対象ファイル: {csv_path}\n")

    # バックアップ作成
    backup_path = create_backup(csv_path)

    # 修正実行
    success = fix_r7gakkaa_039(csv_path)

    if success:
        print(f"\n処理完了")
        print(f"  バックアップ: {backup_path}")
        print(f"  修正ファイル: {csv_path}")
    else:
        print(f"\n処理失敗")

if __name__ == '__main__':
    main()
