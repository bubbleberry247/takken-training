import csv
import sys
import io
import re

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

input_file = 'questionbank_drive_import_katakana.csv'
output_file = 'questionbank_drive_import_formatted.csv'

def format_fill_in_choice(choice_text):
    """
    穴埋め問題の選択肢をフォーマット
    例: 'T V W U ますます安く 高く かわらない 相反する'
    → '（イ）ますます安く（ロ）高く（ハ）かわらない（ニ）相反する'
    例: '逆に高く 高く 悪くなる 相反する'
    → '（イ）逆に高く（ロ）高く（ハ）悪くなる（ニ）相反する'
    """
    # T V W Uを削除
    text = re.sub(r'\bT\b\s*', '', choice_text)
    text = re.sub(r'\bV\b\s*', '', text)
    text = re.sub(r'\bW\b\s*', '', text)
    text = re.sub(r'\bU\b\s*', '', text)

    # 連続するスペースを1つに
    text = re.sub(r'\s+', ' ', text).strip()

    # スペースで分割（4つの単語/フレーズに分割）
    words = text.split()

    # 各単語の前に（イ）（ロ）（ハ）（ニ）を付ける
    labels = ['（イ）', '（ロ）', '（ハ）', '（ニ）']
    formatted_words = []

    for i, word in enumerate(words):
        if i < len(labels):
            formatted_words.append(labels[i] + word)
        else:
            formatted_words.append(word)

    return ''.join(formatted_words)

def is_fill_in_question(stem):
    """問題文が穴埋め問題かどうか判定"""
    return bool(re.search(r'T〜U|（イ）|（ロ）|（ハ）|（ニ）', stem))

with open(input_file, 'r', encoding='utf-8-sig', newline='') as f_in:
    reader = csv.DictReader(f_in)
    fieldnames = reader.fieldnames
    rows = list(reader)

converted_count = 0

for row in rows:
    # 穴埋め問題の場合、全ての選択肢をフォーマット
    if is_fill_in_question(row['stem']):
        for choice_key in ['choiceA', 'choiceB', 'choiceC', 'choiceD']:
            original = row[choice_key]
            if original.strip():  # 空でない場合
                formatted = format_fill_in_choice(original)
                row[choice_key] = formatted
                converted_count += 1

with open(output_file, 'w', encoding='utf-8-sig', newline='') as f_out:
    writer = csv.DictWriter(f_out, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print(f"✅ 選択肢変換完了！")
print(f"変換した選択肢数: {converted_count}個")
print(f"出力ファイル: {output_file}")
