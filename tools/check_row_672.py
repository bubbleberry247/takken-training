import csv
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

with open('questionbank_drive_import_formatted.csv', 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    rows = list(reader)

    # 672行目（ヘッダー除く）
    if len(rows) >= 672:
        row = rows[671]  # 0-indexed
        print(f"問題ID: {row['qId']}")
        print(f"\n選択肢:")
        print(f"  (1) {row['choiceA']}")
        print(f"  (2) {row['choiceB']}")
        print(f"  (3) {row['choiceC']}")
        print(f"  (4) {row['choiceD']}")
