import csv
import sys
import io
import re

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

input_file = 'questionbank_drive_import_fixed_reinforcement.csv'
output_file = 'questionbank_drive_import_fixed_table.csv'

# 選択肢番号マッピング
choice_nums = {
    'choiceA': '１',
    'choiceB': '２',
    'choiceC': '３',
    'choiceD': '４',
}

def format_table_choice(choice_text, labels, choice_key):
    """
    表形式の選択肢をフォーマット
    例: 'コンクリート工 スランプ 圧縮強度試験'
    → '（１）[工種]コンクリート工　[品質特性]スランプ　[試験方法]圧縮強度試験'
    """
    # スペースで分割（複数スペースも考慮）
    parts = re.split(r'\s+', choice_text.strip())

    # ラベル数より少ない場合はそのまま返す
    if len(parts) < len(labels):
        return choice_text

    # ラベル数より多い場合、最後の列を結合
    if len(parts) > len(labels):
        # 最初の(labels数-1)個を取り、残りを結合して最後に追加
        adjusted_parts = parts[:len(labels)-1]
        adjusted_parts.append(' '.join(parts[len(labels)-1:]))
        parts = adjusted_parts

    # フォーマット
    choice_num = choice_nums[choice_key]
    formatted_parts = []
    for i, (label, part) in enumerate(zip(labels, parts)):
        formatted_parts.append(f'[{label}]{part}')

    return f'（{choice_num}）' + '　'.join(formatted_parts)

def is_table_format_question(stem):
    """問題文に列ラベルが含まれているか判定"""
    return bool(re.search(r'\[.+?\]\s+\[.+?\]\s+\[.+?\]', stem))

def extract_labels(stem):
    """問題文から列ラベルを抽出"""
    return re.findall(r'\[(.+?)\]', stem)

with open(input_file, 'r', encoding='utf-8-sig', newline='') as f_in:
    reader = csv.DictReader(f_in)
    fieldnames = reader.fieldnames
    rows = list(reader)

fixed_count = 0

for row in rows:
    stem = row['stem']

    # 表形式問題の場合
    if is_table_format_question(stem):
        labels = extract_labels(stem)

        # 選択肢がスペース区切りの場合のみフォーマット
        for choice_key in ['choiceA', 'choiceB', 'choiceC', 'choiceD']:
            original = row[choice_key]

            # 既にフォーマット済み（（イ）や（１）で始まる）ならスキップ
            if original.startswith('（'):
                continue

            # スペース区切りのデータかチェック
            parts = re.split(r'\s+', original.strip())
            if len(parts) >= len(labels) and len(parts) >= 2:
                formatted = format_table_choice(original, labels, choice_key)
                if formatted != original:
                    row[choice_key] = formatted
                    fixed_count += 1

with open(output_file, 'w', encoding='utf-8-sig', newline='') as f_out:
    writer = csv.DictWriter(f_out, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print(f"✅ 表形式選択肢修正完了！")
print(f"修正した選択肢数: {fixed_count}個")
print(f"出力ファイル: {output_file}")
