import csv
import sys
import io
import re

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

input_file = 'questionbank_drive_import_fixed.csv'
output_file = 'questionbank_drive_import_fixed_variables.csv'

def is_variable_combination_question(stem):
    """
    変数組合せ問題かどうか判定
    例: 「R〜S」「P〜Q」などの変数範囲を含む
    """
    return bool(re.search(r'[A-Z]〜[A-Z]', stem) and '組合せ' in stem)

def extract_variables(stem):
    """
    問題文から変数範囲を抽出
    例: 「R〜S」 → ['R', 'S']（実際はR, T, U, Sの4変数を想定）
    """
    match = re.search(r'([A-Z])〜([A-Z])', stem)
    if match:
        start_var = match.group(1)
        end_var = match.group(2)

        # アルファベット範囲を展開（R〜S → R, S, T, U を想定）
        # 通常は4変数（イロハニに対応）
        # 簡易的に、start_varから4文字を取得
        start_ord = ord(start_var)
        vars_list = []

        # R〜Sの場合、RとSの間にTとUがあると想定
        # 実際には、問題文中に出現する変数を抽出すべきだが、
        # ここでは簡易的に、選択肢の先頭4単語が変数に対応すると仮定

        # 問題文から変数を直接抽出
        all_vars = re.findall(r'\b([A-Z])\b', stem)
        # ユニークな変数を抽出（順序を保持）
        seen = set()
        unique_vars = []
        for v in all_vars:
            if v not in seen and len(v) == 1 and v.isupper():
                seen.add(v)
                unique_vars.append(v)

        return unique_vars[:4]  # 最大4変数

    return []

def format_variable_choice(choice_text, variables):
    """
    変数組合せ選択肢をフォーマット
    元: 'R T U S 工程 新工法 標準 画一的'
    → '[R]工程　[T]新工法　[U]標準　[S]画一的'
    """
    # スペースで分割
    parts = re.split(r'\s+', choice_text.strip())

    # 最初のN個（変数の数）をスキップして、残りを変数に対応させる
    # ただし、選択肢が既に変数を含んでいる場合（R T U S）、それをスキップ

    # パターン1: 'R T U S 工程 新工法...' → 最初の4個が変数
    # パターン2: '工程 新工法...' → 変数なし

    # 最初の部分が全て大文字1文字かチェック
    var_count = 0
    for part in parts:
        if len(part) == 1 and part.isupper():
            var_count += 1
        else:
            break

    if var_count >= len(variables):
        # 変数部分をスキップ
        value_parts = parts[var_count:]
    else:
        # 変数なし
        value_parts = parts

    # 変数の数と値の数が一致しない場合はそのまま返す
    if len(value_parts) < len(variables):
        return choice_text

    # フォーマット
    formatted_parts = []
    for i, var in enumerate(variables):
        if i < len(value_parts):
            formatted_parts.append(f'[{var}]{value_parts[i]}')

    return '　'.join(formatted_parts)

with open(input_file, 'r', encoding='utf-8-sig', newline='') as f_in:
    reader = csv.DictReader(f_in)
    fieldnames = reader.fieldnames
    rows = list(reader)

fixed_count = 0

for row in rows:
    stem = row['stem']

    if is_variable_combination_question(stem):
        variables = extract_variables(stem)

        if variables:
            # 選択肢をフォーマット
            for key in ['choiceA', 'choiceB', 'choiceC', 'choiceD']:
                original = row[key]
                formatted = format_variable_choice(original, variables)

                if formatted != original:
                    row[key] = formatted
                    fixed_count += 1

with open(output_file, 'w', encoding='utf-8-sig', newline='') as f_out:
    writer = csv.DictWriter(f_out, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print(f"✅ 変数組合せ選択肢修正完了！")
print(f"修正した選択肢数: {fixed_count}個")
print(f"出力ファイル: {output_file}")
