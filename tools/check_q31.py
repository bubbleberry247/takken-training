import csv

csv_path = r"C:\ProgramData\Generative AI\Github\doboku-14w-training\tools\questionbank_drive_import.csv"

with open(csv_path, 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row['qId'] == 'R3gakkaB-031':
            print("=== R3gakkaB-031 ===")
            print(f"stem: {row['stem'][:500]}")
            print(f"\nchoiceA: {row['choiceA'][:200]}")
            print(f"\nchoiceB: {row['choiceB'][:200]}")
            break
