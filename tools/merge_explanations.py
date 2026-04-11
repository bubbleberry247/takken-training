# coding: utf-8
"""
プロジェクト2の解説文をプロジェクト1のCSVに統合
"""
import sys
import csv
import json
from pathlib import Path
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

def load_project2_explanations():
    """プロジェクト2の解説文JSONを読み込み"""
    json_path = Path(r"C:\ProgramData\Generative AI\Github\doboku-14w-training\tools\project2_explanations.json")

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    return data['explanations']

def merge_csv_with_explanations(csv_path, explanations):
    """CSVにプロジェクト2の解説文をマージ"""

    # CSVを読み込み
    rows = []
    fieldnames = []

    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for row in reader:
            rows.append(row)

    print(f"読み込んだ行数: {len(rows)}")

    # マージ統計
    stats = {
        'total': len(rows),
        'updated': 0,
        'skipped_already_complete': 0,
        'skipped_no_explanation': 0
    }

    updates = []

    # 各行をチェックして、プロジェクト2の解説があれば追加
    for row in rows:
        qid = row['qId']

        # 既に完全な解説がある場合はスキップ
        has_explain_short = bool(row.get('explainShort', '').strip())
        has_all_choice_explains = all([
            bool(row.get('explainA', '').strip()),
            bool(row.get('explainB', '').strip()),
            bool(row.get('explainC', '').strip()),
            bool(row.get('explainD', '').strip())
        ])

        if has_explain_short and has_all_choice_explains:
            stats['skipped_already_complete'] += 1
            continue

        # プロジェクト2に解説があるかチェック
        if qid in explanations:
            explanation_data = explanations[qid]
            explanation_text = explanation_data['explanation']

            # explainShortが空なら追加
            if not has_explain_short:
                row['explainShort'] = explanation_text

            stats['updated'] += 1
            updates.append({
                'qId': qid,
                'year': explanation_data['year'],
                'original_number': explanation_data['original_number'],
                'updated_fields': ['explainShort'] if not has_explain_short else []
            })
        else:
            stats['skipped_no_explanation'] += 1

    # バックアップ
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = csv_path.parent / f"questionbank_drive_import_backup_{timestamp}.csv"

    print(f"\nバックアップ作成中: {backup_path.name}")
    with open(backup_path, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        with open(csv_path, 'r', encoding='utf-8-sig') as orig:
            reader = csv.DictReader(orig)
            for row in reader:
                writer.writerow(row)

    # 更新後のCSVを書き込み
    print(f"\nCSV更新中: {csv_path.name}")
    with open(csv_path, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return stats, updates

def main():
    print("="*80)
    print("プロジェクト2の解説文をプロジェクト1のCSVに統合")
    print("="*80)

    # プロジェクト2の解説文を読み込み
    print("\n📄 プロジェクト2の解説文を読み込み中...")
    explanations = load_project2_explanations()
    print(f"  読み込み完了: {len(explanations)}問")

    # プロジェクト1のCSVパス
    csv_path = Path(r"C:\ProgramData\Generative AI\Github\doboku-14w-training\tools\questionbank_drive_import.csv")

    if not csv_path.exists():
        print(f"\nエラー: CSVファイルが見つかりません: {csv_path}")
        return

    # マージ実行
    print(f"\n🔄 CSVにマージ中...")
    stats, updates = merge_csv_with_explanations(csv_path, explanations)

    # 結果表示
    print("\n\n" + "="*80)
    print("【統合結果】")
    print("="*80)
    print(f"総問題数: {stats['total']}")
    print(f"更新した問題: {stats['updated']}問")
    print(f"既に完全な解説あり（スキップ）: {stats['skipped_already_complete']}問")
    print(f"プロジェクト2に解説なし（スキップ）: {stats['skipped_no_explanation']}問")

    # 更新した問題の詳細
    if updates:
        print(f"\n更新した問題のサンプル（最初の20問）:")
        for update in updates[:20]:
            print(f"  {update['qId']}: {update['year']} 問{update['original_number']}")

    # 年度別統計
    print(f"\n年度別更新統計:")
    year_stats = {}
    for update in updates:
        year = update['year']
        year_stats[year] = year_stats.get(year, 0) + 1

    for year in sorted(year_stats.keys()):
        print(f"  {year}: {year_stats[year]}問")

    print(f"\n✅ 統合完了！")
    print(f"更新されたCSV: {csv_path}")

if __name__ == "__main__":
    main()
