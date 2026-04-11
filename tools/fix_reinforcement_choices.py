import csv
import sys
import io
import re

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

input_file = 'questionbank_drive_import_fixed_count.csv'
output_file = 'questionbank_drive_import_fixed_reinforcement.csv'

# マッピング
choice_num_map = {
    '1': ('１', '①'),
    '2': ('２', '②'),
    '3': ('３', '③'),
    '4': ('４', '④'),
}

def fix_reinforcement_choice(choice_text):
    """
    鉄筋番号の選択肢を修正
    例: '1D 13' → '（１）①D13'
    """
    match = re.match(r'^(\d+)D\s+(\d+)$', choice_text.strip())
    if match:
        choice_num = match.group(1)
        rebar_num = match.group(2)

        if choice_num in choice_num_map:
            jp_num, circled_num = choice_num_map[choice_num]
            return f'（{jp_num}）{circled_num}D{rebar_num}'

    return choice_text

with open(input_file, 'r', encoding='utf-8-sig', newline='') as f_in:
    reader = csv.DictReader(f_in)
    fieldnames = reader.fieldnames
    rows = list(reader)

fixed_count = 0

for row in rows:
    choices = [row['choiceA'], row['choiceB'], row['choiceC'], row['choiceD']]

    # パターンマッチする選択肢があれば修正
    if any(re.match(r'^\d+D\s+\d+$', choice.strip()) for choice in choices):
        for key in ['choiceA', 'choiceB', 'choiceC', 'choiceD']:
            original = row[key]
            fixed = fix_reinforcement_choice(original)
            if fixed != original:
                row[key] = fixed
                fixed_count += 1

with open(output_file, 'w', encoding='utf-8-sig', newline='') as f_out:
    writer = csv.DictWriter(f_out, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print(f"✅ 鉄筋番号選択肢修正完了！")
print(f"修正した選択肢数: {fixed_count}個")
print(f"出力ファイル: {output_file}")
