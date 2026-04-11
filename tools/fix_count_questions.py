import csv
import sys
import io
import re

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

input_file = 'questionbank_drive_import_final.csv'
output_file = 'questionbank_drive_import_fixed_count.csv'

def is_count_question(stem):
    """数を問う問題かどうか判定"""
    return bool(re.search(r'(正しい|誤っている|該当する|適当な|不適当な).{0,10}(数|個数)は', stem))

def fix_count_choices(row):
    """数を問う問題の選択肢を修正"""
    # 標準的な選択肢に修正
    row['choiceA'] = '（１）１つ'
    row['choiceB'] = '（２）２つ'
    row['choiceC'] = '（３）３つ'
    row['choiceD'] = '（４）４つ'
    return row

with open(input_file, 'r', encoding='utf-8-sig', newline='') as f_in:
    reader = csv.DictReader(f_in)
    fieldnames = reader.fieldnames
    rows = list(reader)

fixed_count = 0

for row in rows:
    if is_count_question(row['stem']):
        # （イ）などが付いている場合もあるので、一律修正
        if not (row['choiceA'] == '（１）１つ' and
                row['choiceB'] == '（２）２つ' and
                row['choiceC'] == '（３）３つ' and
                row['choiceD'] == '（４）４つ'):
            row = fix_count_choices(row)
            fixed_count += 1

with open(output_file, 'w', encoding='utf-8-sig', newline='') as f_out:
    writer = csv.DictWriter(f_out, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print(f"✅ 数を問う問題の選択肢修正完了！")
print(f"修正した問題数: {fixed_count}問")
print(f"出力ファイル: {output_file}")
