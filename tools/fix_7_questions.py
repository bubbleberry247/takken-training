#!/usr/bin/env python3
"""Fix 7 questions in questionbank_drive_import.csv.

Choice OCR issues (4 questions):
1. R1gakkaB-017: choiceB/C/D missing text
2. R1gakkaB-023: choiceA/B missing numbers
3. R6gakkaB-021: choiceA garbled
4. R7gakkaA-005: choiceD garbled (image question - check if acceptable)

Explain label issues (3 questions):
5. R4gakkaA-047: missing 適当/不適当 labels
6. R4gakkaA-051: missing 誤り/正しい labels
7. R4gakkaA-052: missing 適当/不適当 labels
"""
import csv
import sys
import os

CSV_PATH = os.path.join(os.path.dirname(__file__), "questionbank_drive_import.csv")

# Read
with open(CSV_PATH, "r", encoding="utf-8-sig", newline="") as f:
    reader = csv.DictReader(f)
    fieldnames = reader.fieldnames
    rows = list(reader)

changes = []

for row in rows:
    qid = row["qId"]

    # ── Fix 1: R1gakkaB-017 ──
    if qid == "R1gakkaB-017":
        # choiceB: "回の降雨量が30 mm 以上の大雨" → "1回の降雨量が30 mm 以上の大雨"
        old_b = row["choiceB"]
        if old_b.startswith("回の降雨量"):
            row["choiceB"] = "1" + old_b
            changes.append(f"{qid}: choiceB prepended '1' → '{row['choiceB'][:40]}...'")

        # choiceC: "回の降雪量が25 cm 以上の大雪" → "1回の降雪量が25 cm 以上の大雪"
        old_c = row["choiceC"]
        if old_c.startswith("回の降雪量"):
            row["choiceC"] = "1" + old_c
            changes.append(f"{qid}: choiceC prepended '1' → '{row['choiceC'][:40]}...'")

        # choiceD: "震度階級以上の地震" → "中震以上（震度4以上）の地震"
        old_d = row["choiceD"]
        if "震度階級以上" in old_d:
            row["choiceD"] = old_d.replace("震度階級以上の地震", "中震以上（震度4以上）の地震")
            changes.append(f"{qid}: choiceD fixed → '{row['choiceD']}'")

    # ── Fix 2: R1gakkaB-023 ──
    elif qid == "R1gakkaB-023":
        # choiceA: "年以内ごとに回" → "1年以内ごとに1回"
        # Full text: "事業者は,原則として常時使用する労働者に対し,年以内ごとに回,定期に,医師による 健康診断を行わなければならない。"
        old_a = row["choiceA"]
        if "年以内ごとに回" in old_a:
            row["choiceA"] = old_a.replace("年以内ごとに回", "1年以内ごとに1回")
            changes.append(f"{qid}: choiceA fixed → '{row['choiceA'][:60]}...'")

        # choiceB: "週間当たり40時間" → "1週間当たり40時間" and "月当たり100時間" → "1月当たり100時間"
        old_b = row["choiceB"]
        fixed_b = old_b
        if "週間当たり40時間" in fixed_b and not "1週間当たり40時間" in fixed_b:
            fixed_b = fixed_b.replace("週間当たり40時間", "1週間当たり40時間")
        if "月当たり100時間" in fixed_b and not "1月当たり100時間" in fixed_b:
            # Actually from explain: "1ヶ月当たり80時間" - but the choice text intentionally says 100
            # because it's the WRONG answer. The choice uses wrong number on purpose.
            fixed_b = fixed_b.replace("月\n当たり100時間", "1月当たり100時間")
            fixed_b = fixed_b.replace("月当たり100時間", "1月当たり100時間")
        if fixed_b != old_b:
            row["choiceB"] = fixed_b
            changes.append(f"{qid}: choiceB fixed → '{row['choiceB'][:80]}...'")

    # ── Fix 3: R6gakkaB-021 ──
    elif qid == "R6gakkaB-021":
        # choiceA is garbled. From the explainA: "イ：分散化　ロ：市販品　ハ：納期　ニ：部分的"
        # But wait - the explainA says "×不適当です" and the content describes different terms
        # Let me check: explainA = "選択肢1. イ：分散化　　ロ：市販品　　ハ：納期　　ニ：部分的×不適当です。"
        # But current choiceA = "（イ）分類化（ロ）承認図（ハ）品名（ニ）品目別"
        # The explain says choiceA should be (イ)分散化(ロ)市販品(ハ)納期(ニ)部分的
        # Wait, that can't be right - choiceD (correct) already has (ロ)市販品.
        # Let me look at the explains more carefully:
        # explainA: "イ：分散化　ロ：市販品　ハ：納期　ニ：部分的" - but this doesn't match choiceB or choiceC either
        #
        # Actually re-reading the explains from the CSV read:
        # explainA: "選択肢1. イ：分散化　　ロ：市販品　　ハ：納期　　ニ：部分的×不適当です。"
        # explainB: "選択肢2. イ：分散化　　ロ：特注品　　ハ：規格　　ニ：部分的×不適当です。"
        # explainC: "選択肢3. イ：ユニット化　　ロ：特注品　　ハ：納期　　ニ：総合的×不適当です。"
        # explainD: "〇適当です。イ：...ユニット化...ロ：市販品...ハ：規格...ニ：総合的..."
        #
        # So the correct choices according to explains:
        # A: (イ)分散化 (ロ)市販品 (ハ)納期 (ニ)部分的  ← this is what it should be
        # B: (イ)分散化 (ロ)特注品 (ハ)規格 (ニ)部分的  ← current CSV has this correctly
        # C: (イ)ユニット化 (ロ)特注品 (ハ)納期 (ニ)総合的  ← current CSV has this correctly
        # D: (イ)ユニット化 (ロ)市販品 (ハ)規格 (ニ)総合的  ← current CSV has this correctly
        #
        # Current choiceA in CSV: "（イ）分類化（ロ）承認図（ハ）品名（ニ）品目別" - totally garbled
        old_a = row["choiceA"]
        new_a = "（イ）分散化（ロ）市販品（ハ）納期（ニ）部分的"
        if old_a != new_a:
            row["choiceA"] = new_a
            changes.append(f"{qid}: choiceA fixed from garbled '{old_a}' → '{new_a}'")

    # ── Fix 4: R7gakkaA-005 ──
    elif qid == "R7gakkaA-005":
        # Image URL question with formulas. User says: check if image covers choices.
        # The imageUrl is set, so the image shows the formulas.
        # choiceD is "[図]" which is acceptable for image-based questions.
        # Leave as-is.
        changes.append(f"{qid}: SKIPPED - image question, formula garbling is acceptable (imageUrl present)")

    # ── Fix 5: R4gakkaA-047 ──
    elif qid == "R4gakkaA-047":
        correct = row["correct"]  # "D"
        # Current explains don't have explicit labels
        # stem: "適当なものはどれか" → correct=適当, incorrect=不適当
        for label in ["A", "B", "C", "D"]:
            key = f"explain{label}"
            val = row[key]
            if not val:
                continue
            # Check if already has label
            if val.startswith("適当です") or val.startswith("不適当です") or val.startswith("正しい") or val.startswith("誤り"):
                continue
            if label == correct:
                row[key] = "適当です。" + val
                changes.append(f"{qid}: explain{label} prepended '適当です。'")
            else:
                row[key] = "不適当です。" + val
                changes.append(f"{qid}: explain{label} prepended '不適当です。'")

    # ── Fix 6: R4gakkaA-051 ──
    elif qid == "R4gakkaA-051":
        correct = row["correct"]  # "A"
        # stem: "誤っているものはどれか" → correct=誤り, incorrect=正しい
        for label in ["A", "B", "C", "D"]:
            key = f"explain{label}"
            val = row[key]
            if not val:
                continue
            if val.startswith("適当です") or val.startswith("不適当です") or val.startswith("正しい") or val.startswith("誤り"):
                continue
            if label == correct:
                row[key] = "誤りです。" + val
                changes.append(f"{qid}: explain{label} prepended '誤りです。'")
            else:
                row[key] = "正しいです。" + val
                changes.append(f"{qid}: explain{label} prepended '正しいです。'")

    # ── Fix 7: R4gakkaA-052 ──
    elif qid == "R4gakkaA-052":
        correct = row["correct"]  # "B"
        # stem: "作業主任者の選任を必要とする作業はどれか" → correct=適当(必要), incorrect=不適当(不要)
        for label in ["A", "B", "C", "D"]:
            key = f"explain{label}"
            val = row[key]
            if not val:
                continue
            if val.startswith("適当です") or val.startswith("不適当です") or val.startswith("正しい") or val.startswith("誤り"):
                continue
            if label == correct:
                row[key] = "正しいです。" + val
                changes.append(f"{qid}: explain{label} prepended '正しいです。'")
            else:
                row[key] = "誤りです。" + val
                changes.append(f"{qid}: explain{label} prepended '誤りです。'")

# Write
with open(CSV_PATH, "w", encoding="utf-8-sig", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_MINIMAL)
    writer.writeheader()
    writer.writerows(rows)

print(f"\n=== {len(changes)} changes applied ===")
for c in changes:
    print(f"  {c}")
print(f"\nSaved to: {CSV_PATH}")
