"""
fix_15_explanations.py
15問の壊れた解説をkakomonn.comから再取得してCSVを更新する。

使用方法:
  python tools/fix_15_explanations.py          # スクレイプ → CSV更新
  python tools/fix_15_explanations.py --dry-run # スクレイプのみ（CSV変更なし）
"""

import argparse
import csv
import os
import re
import sys
import time
from datetime import datetime
from typing import Optional

import requests
from bs4 import BeautifulSoup

# --- Config ---
DOBOKU_BASE = "https://1dobokusekou.kakomonn.com"
CSV_PATH = r"C:\ProgramData\Generative AI\Github\doboku-14w-training\tools\questionbank_drive_import.csv"
SLEEP_SEC = 1.0

HEADERS_HTTP = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
}

ID_MAP: dict[str, int] = {
    "R2gakkaB": 53685, "R3gakkaA": 58752, "R3gakkaB": 58813,
    "R4gakkaB": 67731, "R5gakkaA": 74716, "R5gakkaB": 74777,
    "R6gakkaB": 78560, "R7gakkaB": 86670,
}

TARGETS = [
    "R2gakkaB-006", "R2gakkaB-012", "R2gakkaB-026", "R2gakkaB-029",
    "R3gakkaA-051", "R3gakkaB-001", "R3gakkaB-006",
    "R4gakkaB-006",
    "R5gakkaA-013", "R5gakkaA-020", "R5gakkaB-026",
    "R6gakkaB-006", "R6gakkaB-022",
    "R7gakkaB-010", "R7gakkaB-011",
]

NUM_TO_LETTER = {1: "A", 2: "B", 3: "C", 4: "D"}


def qid_to_kid(qid: str) -> Optional[int]:
    for prefix, base in ID_MAP.items():
        if qid.startswith(prefix + "-"):
            try:
                return base + int(qid[len(prefix) + 1:])
            except ValueError:
                return None
    return None


def clean_text(text: str) -> str:
    """Clean extracted text: normalize whitespace, remove leading/trailing junk."""
    text = re.sub(r'\s+', ' ', text).strip()
    # Remove leading "選択肢N. " prefix if present (we want just the explanation)
    # Actually, keep it - it's useful context
    return text


def parse_bottom_per_choice(bottom_text: str) -> dict[str, str]:
    """Parse expound-bottom text that contains numbered per-choice explanations.

    Handles patterns like:
      ①...→〇  ②...→✕  ③...→✕  ④...→✕
      1....  2....  3....  4....
    """
    result: dict[str, str] = {}
    # Try circled numbers ①②③④ or regular ①〜④
    pattern = r'([①②③④]|(?:^|\s)([1-4])[\．\.\s])'
    # Split by circled numbers
    parts = re.split(r'(?=[①②③④])', bottom_text)
    num_map = {"①": "A", "②": "B", "③": "C", "④": "D"}

    for part in parts:
        part = part.strip()
        if not part:
            continue
        first_char = part[0]
        if first_char in num_map:
            letter = num_map[first_char]
            # Remove the leading number
            content = part[1:].strip()
            if content:
                result[f"explain{letter}"] = clean_text(content)[:500]

    return result


def fetch_explanation(kid: int) -> dict:
    """Fetch per-choice explanations from kakomonn.com."""
    result = {
        "explainA": "", "explainB": "", "explainC": "", "explainD": "",
        "explainShort": "", "error": None,
    }
    url = f"{DOBOKU_BASE}/questions/{kid}"

    try:
        sess = requests.Session()
        sess.headers.update(HEADERS_HTTP)
        resp = sess.get(url, timeout=15)
        resp.raise_for_status()
        resp.encoding = "utf-8"
        soup = BeautifulSoup(resp.text, "html.parser")

        # Find all expound-wrap sections (there may be multiple posts)
        wraps = soup.select(".expound-wrap")

        if not wraps:
            result["error"] = "no_expound_wrap"
            return result

        # Pick the best wrap: the one with the most expound-1..4 divs
        best_wrap = None
        best_score = -1

        for wrap in wraps:
            score = 0
            total_len = 0
            for n in range(1, 5):
                div = wrap.select_one(f".expound-{n}")
                if div:
                    score += 1
                    txt = div.select_one(".expound-txt")
                    if txt:
                        total_len += len(txt.get_text(strip=True))
            # Prefer: more expound-N divs, then longer total text
            composite = score * 10000 + total_len
            if composite > best_score:
                best_score = composite
                best_wrap = wrap

        if not best_wrap or best_score <= 0:
            result["error"] = "no_expound_choices"
            return result

        # Extract per-choice explanations from best wrap
        for n in range(1, 5):
            letter = NUM_TO_LETTER[n]
            div = best_wrap.select_one(f".expound-{n}")
            if div:
                txt = div.select_one(".expound-txt")
                if txt:
                    result[f"explain{letter}"] = clean_text(txt.get_text(strip=True))[:500]

        # Fallback: if fewer than 3 explainA-D were populated, try expound-bottom
        filled = sum(1 for l in "ABCD" if result[f"explain{l}"])
        if filled < 3:
            bottoms = best_wrap.select(".expound-bottom .expound-txt")
            # Pick the longest bottom text
            if bottoms:
                best_bottom = max(bottoms, key=lambda b: len(b.get_text(strip=True)))
                bottom_text = best_bottom.get_text(strip=True)
                parsed = parse_bottom_per_choice(bottom_text)
                for letter in "ABCD":
                    key = f"explain{letter}"
                    if not result[key] and key in parsed:
                        result[key] = parsed[key]

        # Extract explainShort from the best expound-top
        # Find the expound-top that's the longest and most comprehensive
        tops = best_wrap.select(".expound-top")
        if not tops:
            # Look in parent context
            tops = soup.select(".expound-top")

        if tops:
            best_top = max(tops, key=lambda t: len(t.get_text(strip=True)))
            result["explainShort"] = clean_text(best_top.get_text(strip=True))[:500]

    except Exception as e:
        result["error"] = str(e)[:200]

    return result


def main():
    # Force UTF-8 output
    sys.stdout = __import__('io').TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    parser = argparse.ArgumentParser(description="Fix 15 broken explanations")
    parser.add_argument("--dry-run", action="store_true", help="Scrape only, don't update CSV")
    args = parser.parse_args()

    print(f"=== fix_15_explanations.py ===")
    print(f"Targets: {len(TARGETS)} questions")
    print()

    # Scrape all targets
    scraped: dict[str, dict] = {}
    for i, qid in enumerate(TARGETS):
        kid = qid_to_kid(qid)
        if kid is None:
            print(f"[{i+1}/{len(TARGETS)}] {qid}: SKIP (no ID mapping)")
            continue

        url = f"{DOBOKU_BASE}/questions/{kid}"
        print(f"[{i+1}/{len(TARGETS)}] {qid} (kid={kid})...", end=" ", flush=True)

        data = fetch_explanation(kid)
        scraped[qid] = data

        if data["error"]:
            print(f"ERR: {data['error']}")
        else:
            has_a = "A" if data["explainA"] else "-"
            has_b = "B" if data["explainB"] else "-"
            has_c = "C" if data["explainC"] else "-"
            has_d = "D" if data["explainD"] else "-"
            has_s = "S" if data["explainShort"] else "-"
            print(f"OK [{has_a}{has_b}{has_c}{has_d}{has_s}]")
            # Print preview
            for letter in "ABCD":
                val = data[f"explain{letter}"]
                if val:
                    print(f"  explain{letter}: {val[:100]}...")

        if i < len(TARGETS) - 1:
            time.sleep(SLEEP_SEC)

    print()

    if args.dry_run:
        print("--dry-run: CSV not updated.")
        return

    # Read CSV
    with open(CSV_PATH, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    # Update rows
    updated_count = 0
    for row in rows:
        qid = row["qId"]
        if qid in scraped and scraped[qid]["error"] is None:
            data = scraped[qid]
            changed = False
            for letter in "ABCD":
                key = f"explain{letter}"
                new_val = data[key]
                if new_val:  # Only update if we got content
                    if row.get(key, "") != new_val:
                        row[key] = new_val
                        changed = True
            if data["explainShort"]:
                if row.get("explainShort", "") != data["explainShort"]:
                    row["explainShort"] = data["explainShort"]
                    changed = True
            if changed:
                row["updatedAt"] = datetime.now().strftime("%Y-%m-%d")
                updated_count += 1

    # Backup original
    backup_path = CSV_PATH.replace(".csv", f"_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
    with open(CSV_PATH, "rb") as f:
        original_bytes = f.read()
    with open(backup_path, "wb") as f:
        f.write(original_bytes)
    print(f"Backup: {backup_path}")

    # Write updated CSV
    with open(CSV_PATH, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Updated: {updated_count}/{len(TARGETS)} questions in {CSV_PATH}")


if __name__ == "__main__":
    main()
