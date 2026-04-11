import csv
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

with open('questionbank_drive_import_fixed.csv', 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)

    print("サンプルデータ（最初の3行）:\n")
    for i, row in enumerate(reader):
        if i >= 3:
            break
        print(f"--- 問題 {i+1} ---")
        print(f"qId: {row['qId']}")
        print(f"segmentId: {row['segmentId']}")
        print(f"source_ref: {row['source_ref']}")
        print(f"tag1: {row['tag1']}")
        print(f"tag2: {row['tag2']}")
        print(f"tag3: {row['tag3']}")
        print()
