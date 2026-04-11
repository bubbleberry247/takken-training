import csv
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

with open('questionbank_drive_import_formatted.csv', 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row['qId'] == 'R7gakkaB-026':
            print("【変換後の選択肢】")
            print(f"（１）{row['choiceA']}")
            print(f"（２）{row['choiceB']}")
            print(f"（３）{row['choiceC']}")
            print(f"（４）{row['choiceD']}")
            break
