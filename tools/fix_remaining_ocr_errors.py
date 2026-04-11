#!/usr/bin/env python3
"""
残りのOCR誤変換修正スクリプト

修正内容:
1. R7gakkaA-016 choiceA: `^m 当たり^個` → `1m² 当たり1個`
2. R7gakkaA-026 choiceB: ``〜a%` → `3〜5%`
3. R7gakkaA-026 choiceC: `^層` → `1層`
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

def fix_remaining_errors(csv_path):
    """残りのOCR誤変換を修正"""
    rows = []
    fixed_count = 0

    # CSV読み込み
    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames

        for row in reader:
            # R7gakkaA-016の修正
            if row['qId'] == 'R7gakkaA-016':
                print(f"\n{'='*80}")
                print(f"修正対象: {row['qId']}")
                print(f"{'='*80}")

                original = row['choiceA']
                # ^m → 1m²
                row['choiceA'] = row['choiceA'].replace('^m', '1m²')
                # ^個 → 1個
                row['choiceA'] = row['choiceA'].replace('^個', '1個')

                if original != row['choiceA']:
                    print(f"\n[choiceA修正]")
                    print(f"  修正前: {original}")
                    print(f"  修正後: {row['choiceA']}")
                    fixed_count += 1

                # explainAも同様に修正
                if '^m' in row.get('explainA', '') or '^個' in row.get('explainA', ''):
                    original_ea = row['explainA']
                    row['explainA'] = row['explainA'].replace('^m', '1m²')
                    row['explainA'] = row['explainA'].replace('^個', '1個')
                    if original_ea != row['explainA']:
                        print(f"\n[explainA修正]")
                        print(f"  修正前: {original_ea[:150]}...")
                        print(f"  修正後: {row['explainA'][:150]}...")

            # R7gakkaA-026の修正
            if row['qId'] == 'R7gakkaA-026':
                print(f"\n{'='*80}")
                print(f"修正対象: {row['qId']}")
                print(f"{'='*80}")

                # choiceB: `〜a% → 3〜5%
                if 'choiceB' in row and '`' in row['choiceB']:
                    original_b = row['choiceB']
                    row['choiceB'] = row['choiceB'].replace('`〜a%', '3〜5%')
                    if original_b != row['choiceB']:
                        print(f"\n[choiceB修正]")
                        print(f"  修正前: {original_b}")
                        print(f"  修正後: {row['choiceB']}")
                        fixed_count += 1

                # choiceC: ^層 → 1層
                if 'choiceC' in row and '^層' in row['choiceC']:
                    original_c = row['choiceC']
                    row['choiceC'] = row['choiceC'].replace('^層', '1層')
                    if original_c != row['choiceC']:
                        print(f"\n[choiceC修正]")
                        print(f"  修正前: {original_c}")
                        print(f"  修正後: {row['choiceC']}")
                        fixed_count += 1

                # explainBも修正
                if '`〜a%' in row.get('explainB', ''):
                    original_eb = row['explainB']
                    row['explainB'] = row['explainB'].replace('`〜a%', '3〜5％')
                    if original_eb != row['explainB']:
                        print(f"\n[explainB修正]")
                        print(f"  修正前: {original_eb[:150]}...")
                        print(f"  修正後: {row['explainB'][:150]}...")

                # explainCも修正
                if '^層' in row.get('explainC', ''):
                    original_ec = row['explainC']
                    row['explainC'] = row['explainC'].replace('^層', '1層')
                    if original_ec != row['explainC']:
                        print(f"\n[explainC修正]")
                        print(f"  修正前: {original_ec[:150]}...")
                        print(f"  修正後: {row['explainC'][:150]}...")

            rows.append(row)

    # CSV書き込み
    with open(csv_path, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\n{'='*80}")
    print(f"✓ 修正完了: {csv_path}")
    print(f"  修正件数: {fixed_count}件")
    print(f"{'='*80}\n")
    return fixed_count > 0

def main():
    csv_path = "C:/ProgramData/Generative AI/Github/doboku-14w-training/tools/questionbank_drive_import.csv"

    print(f"残りのOCR誤変換修正開始...")
    print(f"対象ファイル: {csv_path}\n")

    # バックアップ作成
    backup_path = create_backup(csv_path)

    # 修正実行
    success = fix_remaining_errors(csv_path)

    if success:
        print(f"\n処理完了")
        print(f"  バックアップ: {backup_path}")
        print(f"  修正ファイル: {csv_path}")
    else:
        print(f"\n修正対象が見つかりませんでした")

if __name__ == '__main__':
    main()
