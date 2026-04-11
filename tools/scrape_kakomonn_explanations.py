"""
scrape_kakomonn_explanations.py
kakomonn.com から選択肢ごとの詳細解説を取得し、QB解説と文章レベルで突き合わせる。

使用方法:
  python scrape_kakomonn_explanations.py --target R4gakkaB   # 特定セグメントのみ
  python scrape_kakomonn_explanations.py --all                # 全682問
  python scrape_kakomonn_explanations.py --compare            # 取得済みCSVとQB比較のみ
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

DOBOKU_BASE = "https://1dobokusekou.kakomonn.com"
SLEEP_SEC = 1.0
OUTPUT_DIR = r"C:\tmp"

HEADERS_HTTP = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
}

ID_MAP: dict[str, int] = {
    "R1gakkaA": 47838, "R1gakkaB": 47899,
    "R2gakkaA": 53624, "R2gakkaB": 53685,
    "R3gakkaA": 58752, "R3gakkaB": 58813,
    "R4gakkaA": 67670, "R4gakkaB": 67731,
    "R5gakkaA": 74716, "R5gakkaB": 74777,
    "R6gakkaA": 78494, "R6gakkaB": 78560,
    "R7gakkaA": 86604, "R7gakkaB": 86670,
}

NUM_TO_LETTER = {1: "A", 2: "B", 3: "C", 4: "D"}


def qid_to_kid(qid: str) -> Optional[int]:
    for prefix, base in ID_MAP.items():
        if qid.startswith(prefix + "-"):
            try:
                return base + int(qid[len(prefix) + 1:])
            except ValueError:
                return None
    return None


def fetch_full_explanation(kid: int) -> dict:
    """正解値 + 選択肢ごとの詳細解説を取得"""
    result = {"correct": None, "explainA": "", "explainB": "", "explainC": "", "explainD": "",
              "explainShort": "", "raw_text": "", "error": None}
    url = f"{DOBOKU_BASE}/questions/{kid}"

    try:
        sess = requests.Session()
        sess.headers.update(HEADERS_HTTP)
        resp = sess.get(url, timeout=15)
        resp.raise_for_status()
        resp.encoding = "utf-8"
        soup = BeautifulSoup(resp.text, "html.parser")

        # CSRF token
        token_el = soup.select_one('input[name="_token"]')
        if not token_el:
            result["error"] = "no_csrf"
            return result
        token = token_el["value"]

        # POST answer to get correct answer number
        resp2 = sess.post(
            f"{DOBOKU_BASE}/questions/answer",
            data={"strAnswerData": "1-", "intStudyRandumId": str(kid),
                  "intIdCategoryFlag": "1", "_token": token},
            headers={"X-Requested-With": "XMLHttpRequest", "Referer": url},
            timeout=15,
        )
        resp2.raise_for_status()
        data = resp2.json()
        m = re.search(r'ctr_box_09["\s>]+\s*(\d+)\s*<', data.get("response_data03", ""))
        if m:
            result["correct"] = int(m.group(1))

        # Extract explanation from HTML
        # Try multiple selectors
        expound = soup.select_one(".expound-txt")
        if not expound:
            expound = soup.select_one(".sect_commentary .text")
        if not expound:
            # Try after-answer page
            resp3 = sess.get(url, timeout=15)
            resp3.encoding = "utf-8"
            soup2 = BeautifulSoup(resp3.text, "html.parser")
            expound = soup2.select_one(".expound-txt")

        if expound:
            # Get all text content
            raw = expound.get_text(separator="\n", strip=True)
            result["raw_text"] = raw[:1000]

            # Parse per-choice explanations
            # Pattern 1: "1．" "2．" "3．" "4．" (full-width)
            # Pattern 2: "1." "2." "3." "4." (half-width)
            # Pattern 3: "選択肢1." "選択肢2." etc.
            choice_pattern = r'(?:選択肢)?([１1２2３3４4])[\．\.]'
            splits = list(re.finditer(choice_pattern, raw))

            if splits:
                for i, m in enumerate(splits):
                    end = splits[i + 1].start() if i + 1 < len(splits) else len(raw)
                    choice_num = m.group(1)
                    # Normalize to 1-4
                    num_map = {"１": 1, "1": 1, "２": 2, "2": 2, "３": 3, "3": 3, "４": 4, "4": 4}
                    n = num_map.get(choice_num, 0)
                    if 1 <= n <= 4:
                        key = f"explain{NUM_TO_LETTER[n]}"
                        result[key] = raw[m.start():end].strip()[:500]

            # explainShort: first 200 chars of raw
            result["explainShort"] = raw[:200].replace("\n", " ")

    except Exception as e:
        result["error"] = str(e)[:100]

    return result


def scrape_segment(segment: str, qb_rows: dict) -> list[dict]:
    """指定セグメントの全問をスクレイピング"""
    results = []
    questions = [(qid, row) for qid, row in sorted(qb_rows.items()) if qid.startswith(segment + "-")]

    for i, (qid, row) in enumerate(questions):
        kid = qid_to_kid(qid)
        if not kid:
            results.append({"qId": qid, "status": "SKIP"})
            continue

        print(f"\r  [{i+1}/{len(questions)}] {qid} (ID={kid})", end="", flush=True)
        fetched = fetch_full_explanation(kid)

        if fetched["error"]:
            results.append({"qId": qid, "status": "ERR", "error": fetched["error"]})
        else:
            results.append({
                "qId": qid,
                "status": "OK",
                "km_correct": NUM_TO_LETTER.get(fetched["correct"], "?"),
                "qb_correct": row.get("correct", ""),
                "km_explainA": fetched["explainA"],
                "km_explainB": fetched["explainB"],
                "km_explainC": fetched["explainC"],
                "km_explainD": fetched["explainD"],
                "km_explainShort": fetched["explainShort"],
                "qb_explainA": row.get("explainA", ""),
                "qb_explainShort": row.get("explainShort", ""),
            })

        time.sleep(SLEEP_SEC)

    print()
    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", help="Segment to scrape (e.g. R4gakkaB)")
    parser.add_argument("--all", action="store_true", help="Scrape all segments")
    args = parser.parse_args()

    # Load QB
    qb_csv = r"C:\ProgramData\Generative AI\Github\doboku-14w-training\tools\questionbank_drive_import.csv"
    qb = {}
    with open(qb_csv, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            qb[row["qId"]] = row

    if args.target:
        segments = [args.target]
    elif args.all:
        segments = sorted(set(re.match(r"(R\dgakka[AB])", qid).group(1)
                              for qid in qb if re.match(r"R\dgakka[AB]", qid)))
    else:
        parser.print_help()
        return

    all_results = []
    for seg in segments:
        print(f"\n=== {seg} ===")
        results = scrape_segment(seg, qb)
        all_results.extend(results)

        ok = sum(1 for r in results if r["status"] == "OK")
        err = sum(1 for r in results if r["status"] == "ERR")
        with_expl = sum(1 for r in results if r.get("km_explainA", "").strip())
        print(f"  OK={ok}, ERR={err}, explainA取得={with_expl}")

    # Save CSV
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = os.path.join(OUTPUT_DIR, f"kakomonn_full_explanations_{ts}.csv")
    fieldnames = ["qId", "status", "km_correct", "qb_correct",
                  "km_explainA", "km_explainB", "km_explainC", "km_explainD",
                  "km_explainShort", "qb_explainA", "qb_explainShort", "error"]
    with open(out_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(all_results)

    print(f"\n保存: {out_path}")
    total_ok = sum(1 for r in all_results if r["status"] == "OK")
    total_expl = sum(1 for r in all_results if r.get("km_explainA", "").strip())
    print(f"合計: {total_ok} OK, explainA取得={total_expl}/{total_ok}")


if __name__ == "__main__":
    main()
