import csv
import sys
import io
import re

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 数字→丸数字の変換マッピング
circled_numbers = {
    '1': '①',
    '2': '②',
    '3': '③',
    '4': '④',
    '5': '⑤',
    '6': '⑥',
    '7': '⑦',
    '8': '⑧',
    '9': '⑨',
}

def convert_combination_choice(choice_text):
    """
    組み合わせ問題の選択肢を変換
    例: '12' → '①②', '234' → '②③④'
    """
    # 短い数字の並び（1〜4文字の数字のみ）の場合のみ変換
    if re.match(r'^\d{1,4}$', choice_text.strip()):
        result = ''
        for char in choice_text.strip():
            result += circled_numbers.get(char, char)
        return result
    return choice_text

def is_combination_question(stem):
    """組み合わせ問題かどうか判定"""
    return bool(re.search(r'組合せ|組み合わせ', stem))

input_file = 'questionbank_drive_import_formatted.csv'
output_file = 'questionbank_drive_import_final.csv'

with open(input_file, 'r', encoding='utf-8-sig', newline='') as f_in:
    reader = csv.DictReader(f_in)
    fieldnames = reader.fieldnames
    rows = list(reader)

converted_count = 0

for row in rows:
    # 組み合わせ問題の場合、選択肢を変換
    if is_combination_question(row['stem']):
        for choice_key in ['choiceA', 'choiceB', 'choiceC', 'choiceD']:
            original = row[choice_key]
            if original.strip():
                converted = convert_combination_choice(original)
                if converted != original:
                    row[choice_key] = converted
                    converted_count += 1

with open(output_file, 'w', encoding='utf-8-sig', newline='') as f_out:
    writer = csv.DictWriter(f_out, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print(f"✅ 組み合わせ問題の選択肢変換完了！")
print(f"変換した選択肢数: {converted_count}個")
print(f"出力ファイル: {output_file}")
