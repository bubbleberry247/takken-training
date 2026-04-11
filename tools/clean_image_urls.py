import csv
import sys
import io
from pathlib import Path

# UTF-8出力設定
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# ローカルに存在する画像ファイルのセット
images_dir = Path("C:/ProgramData/Generative AI/Github/doboku-14w-training/images")
existing_images = set(f.name for f in images_dir.glob("*.png"))

print(f"ローカルに存在する画像ファイル: {len(existing_images)}個")

# CSVを読み込み
input_file = "questionbank_drive_import_fixed.csv"
output_file = "questionbank_drive_import_cleaned.csv"

with open(input_file, 'r', encoding='utf-8-sig', newline='') as f_in:
    reader = csv.DictReader(f_in)
    fieldnames = reader.fieldnames
    rows = list(reader)

# imageUrlを修正
cleared = 0
kept = 0

for row in rows:
    img_url = row.get('imageUrl', '')
    if img_url and '.png' in img_url:
        # URLからファイル名を抽出
        filename = img_url.split('/')[-1]

        # ローカルに存在しない場合、imageUrlを空にする
        if filename not in existing_images:
            row['imageUrl'] = ''
            cleared += 1
        else:
            kept += 1

# 新しいCSVに書き出し
with open(output_file, 'w', encoding='utf-8-sig', newline='') as f_out:
    writer = csv.DictWriter(f_out, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print(f"✅ imageUrlを保持: {kept}行")
print(f"❌ imageUrlを削除: {cleared}行")
print(f"📄 出力ファイル: {output_file}")
