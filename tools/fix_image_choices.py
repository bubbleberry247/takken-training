import csv
import sys
import io
import re

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

input_file = 'questionbank_drive_import_fixed_table.csv'
output_file = 'questionbank_drive_import_fixed_image.csv'
image_choices_list_file = 'image_choices_list.csv'

# 選択肢番号マッピング
choice_nums = ['１', '２', '３', '４']

def is_image_choice_question(row):
    """
    図表選択肢または数式選択肢の問題かどうか判定
    """
    stem = row['stem']
    choices = [row['choiceA'], row['choiceB'], row['choiceC'], row['choiceD']]

    # パターン1: 選択肢が「（図」で始まる、または「(図」で始まる
    if any(c.strip().startswith('（図') or c.strip().startswith('(図') for c in choices):
        return True, 'diagram'

    # パターン2: 選択肢に数式記号を含む（=, ×, π, ρ, σ）
    all_choices_text = ''.join(choices)
    if (('=' in all_choices_text and ('π' in all_choices_text or 'ρ' in all_choices_text or 'σ' in all_choices_text)) or
        ('Q =' in all_choices_text)):
        return True, 'formula'

    # パターン3: 問題文に「下図」があり、全選択肢が非常に短い（20文字以内）
    if '下図' in stem and all(len(c.strip()) < 20 for c in choices):
        # ただし、既に（１）などで統一されている場合は除外
        if all(c.strip() in ['（１）', '（２）', '（３）', '（４）'] for c in choices):
            return False, None
        return True, 'diagram_short'

    return False, None

def standardize_image_choices(row):
    """
    選択肢を（１）（２）（３）（４）に統一
    """
    for i, key in enumerate(['choiceA', 'choiceB', 'choiceC', 'choiceD']):
        row[key] = f'（{choice_nums[i]}）'
    return row

with open(input_file, 'r', encoding='utf-8-sig', newline='') as f_in:
    reader = csv.DictReader(f_in)
    fieldnames = reader.fieldnames
    rows = list(reader)

fixed_count = 0
image_choices_list = []

for i, row in enumerate(rows, 1):
    is_image, type_ = is_image_choice_question(row)

    if is_image:
        # 問題リストに追加
        image_choices_list.append({
            'row': i,
            'qId': row['qId'],
            'type': type_,
            'stem': row['stem'][:100] + '...',
            'original_choiceA': row['choiceA'],
            'original_choiceB': row['choiceB'],
            'original_choiceC': row['choiceC'],
            'original_choiceD': row['choiceD'],
        })

        # 選択肢を統一
        row = standardize_image_choices(row)
        fixed_count += 1

# メインCSVを出力
with open(output_file, 'w', encoding='utf-8-sig', newline='') as f_out:
    writer = csv.DictWriter(f_out, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

# 画像選択肢問題リストを出力
with open(image_choices_list_file, 'w', encoding='utf-8-sig', newline='') as f_list:
    list_fieldnames = ['row', 'qId', 'type', 'stem', 'original_choiceA', 'original_choiceB', 'original_choiceC', 'original_choiceD']
    writer = csv.DictWriter(f_list, fieldnames=list_fieldnames)
    writer.writeheader()
    writer.writerows(image_choices_list)

print(f"✅ 図表・数式選択肢修正完了！")
print(f"修正した問題数: {fixed_count}問")
print(f"出力ファイル: {output_file}")
print(f"画像選択肢リスト: {image_choices_list_file}")
