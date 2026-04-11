"""
画像ファイル名をQuestionBank qId形式に変換してコピーする

変換ルール:
- R7_gakkaA1.png → R7gakkaA-001.png
- R7_gakkaA25_選択肢1.png → R7gakkaA-025_choice1.png
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from pathlib import Path
import shutil
import re

SOURCE_DIR = Path(r"C:\Users\masam\Desktop\KeyenceRK\１級土木施工管理技術検定愛一時検定_eラーニングサイト\pics")
TARGET_DIR = Path(__file__).parent.parent / "images"

def convert_filename(original_name: str) -> str:
    """
    ファイル名を変換

    例:
    R7_gakkaA1.png → R7gakkaA-001.png
    R7_gakkaA25_選択肢1.png → R7gakkaA-025_choice1.png
    R6_gakkaA5_選択肢.png → R6gakkaA-005_choice.png
    """
    # 拡張子を分離
    stem = Path(original_name).stem
    suffix = Path(original_name).suffix

    # パターン1: R7_gakkaA1.png
    pattern1 = r'^(R\d+)_(gakka[AB])(\d+)$'
    match1 = re.match(pattern1, stem)
    if match1:
        year = match1.group(1)
        gakka = match1.group(2)
        num = match1.group(3).zfill(3)  # ゼロパディング
        return f"{year}{gakka}-{num}{suffix}"

    # パターン2: R7_gakkaA25_選択肢1.png
    pattern2 = r'^(R\d+)_(gakka[AB])(\d+)_選択肢(\d*)$'
    match2 = re.match(pattern2, stem)
    if match2:
        year = match2.group(1)
        gakka = match2.group(2)
        num = match2.group(3).zfill(3)
        choice_num = match2.group(4)
        if choice_num:
            return f"{year}{gakka}-{num}_choice{choice_num}{suffix}"
        else:
            return f"{year}{gakka}-{num}_choice{suffix}"

    # 変換できない場合はそのまま
    return original_name

def main():
    if not SOURCE_DIR.exists():
        print(f"❌ Source directory not found: {SOURCE_DIR}")
        return

    TARGET_DIR.mkdir(parents=True, exist_ok=True)

    # 変換マッピングを作成
    mappings = []
    for src_file in SOURCE_DIR.glob("*.png"):
        new_name = convert_filename(src_file.name)
        target_file = TARGET_DIR / new_name
        mappings.append({
            'original': src_file.name,
            'new': new_name,
            'src_path': src_file,
            'target_path': target_file
        })

    # マッピング表示
    print(f"📊 Total files: {len(mappings)}")
    print(f"📂 Source: {SOURCE_DIR}")
    print(f"📂 Target: {TARGET_DIR}")
    print()

    # サンプル表示（最初の10件）
    print("📋 Sample mappings:")
    for m in mappings[:10]:
        print(f"  {m['original']:40} → {m['new']}")
    if len(mappings) > 10:
        print(f"  ... and {len(mappings) - 10} more")
    print()

    # コピー実行
    copied = 0
    skipped = 0

    for m in mappings:
        if m['target_path'].exists():
            skipped += 1
        else:
            shutil.copy2(m['src_path'], m['target_path'])
            copied += 1

    print(f"✅ Copied: {copied} files")
    print(f"⏭️  Skipped (already exists): {skipped} files")
    print()

    # 変換マッピングをCSVに保存
    mapping_csv = TARGET_DIR / "image_mapping.csv"
    with mapping_csv.open('w', encoding='utf-8') as f:
        f.write("original_name,new_name,qId\n")
        for m in mappings:
            # qIdを抽出（拡張子と_choice部分を除去）
            qid = m['new'].replace('.png', '').split('_choice')[0]
            f.write(f"{m['original']},{m['new']},{qid}\n")

    print(f"📄 Mapping CSV saved: {mapping_csv}")

if __name__ == "__main__":
    main()
