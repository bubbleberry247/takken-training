import csv
import sys
import io
import re

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 変換マッピング
replacements = {
    ' T ': ' （イ） ',
    ' V ': ' （ロ） ',
    ' W ': ' （ハ） ',
    ' U ': ' （ニ） ',
    'T ': '（イ） ',
    ' T': ' （イ）',
    'V ': '（ロ） ',
    ' V': ' （ロ）',
    'W ': '（ハ） ',
    ' W': ' （ハ）',
    'U ': '（ニ） ',
    ' U': ' （ニ）',
}

input_file = 'questionbank_drive_import_fixed.csv'
output_file = 'questionbank_drive_import_katakana.csv'

with open(input_file, 'r', encoding='utf-8-sig', newline='') as f_in:
    reader = csv.DictReader(f_in)
    fieldnames = reader.fieldnames
    rows = list(reader)

converted_count = 0

for row in rows:
    # stem（問題文）を変換
    original_stem = row['stem']
    new_stem = original_stem

    for old, new in replacements.items():
        new_stem = new_stem.replace(old, new)

    if new_stem != original_stem:
        row['stem'] = new_stem
        converted_count += 1

with open(output_file, 'w', encoding='utf-8-sig', newline='') as f_out:
    writer = csv.DictWriter(f_out, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print(f"✅ 変換完了！")
print(f"変換した問題数: {converted_count}問")
print(f"出力ファイル: {output_file}")
