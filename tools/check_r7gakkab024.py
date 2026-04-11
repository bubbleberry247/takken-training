import csv
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

with open('questionbank_drive_import_formatted.csv', 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)

    for row in reader:
        if row['qId'] == 'R7gakkaB-024':
            print(f"問題ID: {row['qId']}")
            print(f"\n問題文（先頭100文字）: {row['stem'][:100]}...")
            print(f"\n選択肢:")
            print(f"  (1) {row['choiceA']}")
            print(f"  (2) {row['choiceB']}")
            print(f"  (3) {row['choiceC']}")
            print(f"  (4) {row['choiceD']}")
            break
