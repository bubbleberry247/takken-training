import csv
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

with open('questionbank_drive_import_fixed.csv', 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    rows = list(reader)
    last_row = rows[-1]

    print(f"問題ID: {last_row['qId']}")
    print(f"問題文（先頭100文字）: {last_row['stem'][:100]}...")
    print(f"\n選択肢:")
    print(f"  A: {last_row['choiceA']}")
    print(f"  B: {last_row['choiceB']}")
    print(f"  C: {last_row['choiceC']}")
    print(f"  D: {last_row['choiceD']}")
