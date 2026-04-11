import csv
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

with open('questionbank_drive_import_fixed.csv', 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if '工程管理' in row['stem'] and 'T〜U' in row['stem']:
            print(f"問題ID: {row['qId']}")
            print(f"問題文（先頭80文字）: {row['stem'][:80]}...")
            print(f"\n選択肢:")
            print(f"  A: {row['choiceA']}")
            print(f"  B: {row['choiceB']}")
            print(f"  C: {row['choiceC']}")
            print(f"  D: {row['choiceD']}")
            print(f"\n正解: {row['correct']}")
            break
