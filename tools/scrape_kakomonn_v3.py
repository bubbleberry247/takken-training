"""
scrape_kakomonn_v3.py
kakomonn.com 全問照合スクリプト（土木 + 建築）

正解値と解説の両方をスクレイピングし、QB CSV と突き合わせる。

使用方法:
  python scrape_kakomonn_v3.py --verify          # 照合のみ（CSV変更なし）
  python scrape_kakomonn_v3.py --verify --archi   # 建築も照合
  python scrape_kakomonn_v3.py --dry-run          # IDマッピング確認のみ
"""

import argparse
import csv
import json
import os
import re
import sys
import time
from datetime import datetime
from typing import Optional

import requests
from bs4 import BeautifulSoup

# -------------------------------------------------------------------
# 設定
# -------------------------------------------------------------------
DOBOKU_CSV = r"C:\ProgramData\Generative AI\Github\doboku-14w-training\tools\questionbank_drive_import.csv"
ARCHI_CSV = r"C:\Users\owner\KeyenceRK\小テスト作成\question_master\question_master.csv"
REPORT_DIR = r"C:\tmp"
ENCODING = "utf-8"
SLEEP_SEC = 1.0

DOBOKU_BASE = "https://1dobokusekou.kakomonn.com"
ARCHI_BASE = "https://kenchikusekou1.kakomonn.com"

HEADERS_HTTP = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
}

# -------------------------------------------------------------------
# IDマッピング
# -------------------------------------------------------------------
DOBOKU_ID_MAP: dict[str, int] = {
    "R1gakkaA": 47838, "R1gakkaB": 47899,
    "R2gakkaA": 53624, "R2gakkaB": 53685,
    "R3gakkaA": 58752, "R3gakkaB": 58813,
    "R4gakkaA": 67670, "R4gakkaB": 67731,
    "R5gakkaA": 74716, "R5gakkaB": 74777,
    "R6gakkaA": 78494, "R6gakkaB": 78560,  # gakkaA: 78495-78560(Q1-66), gakkaB: 78561-78595(Q67-101)
    "R7gakkaA": 86604, "R7gakkaB": 86670,
}

ARCHI_ID_MAP: dict[str, int] = {
    "R5": 71578,  # R5-AM-01=71579, R5-PM-45=71623
    "R6": 77540,
    "R7": 86705,
}

NUM_TO_LETTER = {1: "A", 2: "B", 3: "C", 4: "D", 5: "E"}


def doboku_qid_to_kid(qid: str) -> Optional[int]:
    for prefix, base in DOBOKU_ID_MAP.items():
        if qid.startswith(prefix + "-"):
            try:
                n = int(qid[len(prefix) + 1:])
                return base + n
            except ValueError:
                return None
    return None


def archi_qid_to_kid(qid: str) -> Optional[int]:
    """R5-AM-01 -> 71579, R5-PM-45 -> 71623"""
    m = re.match(r"(R[567])-(AM|PM)-(\d+)", qid)
    if not m:
        return None
    year, _, qno = m.group(1), m.group(2), int(m.group(3))
    base = ARCHI_ID_MAP.get(year)
    if base is None:
        return None
    return base + qno


# -------------------------------------------------------------------
# スクレイピング
# -------------------------------------------------------------------
def fetch_answer_and_explanation(base_url: str, kid: int) -> dict:
    """正解値と解説を取得"""
    result = {"correct": None, "explanation": None, "error": None}
    url = f"{base_url}/questions/{kid}"

    try:
        # Step 1: GET page for CSRF token
        sess = requests.Session()
        sess.headers.update(HEADERS_HTTP)
        resp = sess.get(url, timeout=15)
        resp.raise_for_status()
        resp.encoding = "utf-8"

        soup = BeautifulSoup(resp.text, "html.parser")
        token_input = soup.select_one('input[name="_token"]')
        if not token_input:
            result["error"] = "no_csrf"
            return result
        token = token_input["value"]

        # Step 2: POST answer to get correct answer
        answer_url = f"{base_url}/questions/answer"
        post_data = {
            "strAnswerData": "1-",
            "intStudyRandumId": str(kid),
            "intIdCategoryFlag": "1",
            "_token": token,
        }
        post_headers = {
            "X-Requested-With": "XMLHttpRequest",
            "Content-Type": "application/x-www-form-urlencoded",
            "Referer": url,
        }
        resp2 = sess.post(answer_url, data=post_data, headers=post_headers, timeout=15)
        resp2.raise_for_status()

        data = resp2.json()
        # Extract correct answer from response_data03
        html03 = data.get("response_data03", "")
        m = re.search(r'ctr_box_09["\s>]+\s*(\d+)\s*<', html03)
        if m:
            result["correct"] = int(m.group(1))

        # Step 3: Get explanation from page HTML
        expound = soup.select_one(".expound-txt")
        if expound:
            paragraphs = [p.get_text(strip=True) for p in expound.find_all("p") if p.get_text(strip=True)]
            result["explanation"] = "\n".join(paragraphs)[:500]

    except requests.RequestException as e:
        result["error"] = str(e)[:80]
    except (json.JSONDecodeError, KeyError) as e:
        result["error"] = f"parse: {e}"

    return result


# -------------------------------------------------------------------
# 照合
# -------------------------------------------------------------------
def verify_doboku(csv_path: str) -> list[dict]:
    """土木全問照合"""
    rows = []
    with open(csv_path, encoding=ENCODING) as f:
        for row in csv.DictReader(f):
            rows.append(row)

    results = []
    total = len(rows)

    for i, row in enumerate(rows):
        qid = row.get("qId", "")
        kid = doboku_qid_to_kid(qid)
        qb_correct = row.get("correct", "")
        qb_explain = row.get("explainShort", "")[:50]

        if kid is None:
            results.append({"qId": qid, "status": "SKIP", "detail": "no_id_map"})
            continue

        print(f"\r[{i+1}/{total}] {qid} (ID={kid})", end="", flush=True)

        fetched = fetch_answer_and_explanation(DOBOKU_BASE, kid)

        if fetched["error"]:
            results.append({"qId": qid, "status": "ERR", "detail": fetched["error"]})
        else:
            km_correct_num = fetched["correct"]
            km_correct = NUM_TO_LETTER.get(km_correct_num, "?") if km_correct_num else "?"
            km_expl = (fetched["explanation"] or "")[:50]

            if km_correct == qb_correct:
                status = "OK"
            else:
                status = "NG"

            results.append({
                "qId": qid,
                "status": status,
                "qb_correct": qb_correct,
                "km_correct": km_correct,
                "km_expl_preview": km_expl,
                "qb_expl_preview": qb_explain,
            })

        time.sleep(SLEEP_SEC)

    print()
    return results


def verify_archi(csv_path: str) -> list[dict]:
    """建築全問照合"""
    rows = []
    with open(csv_path, encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            rows.append(row)

    # archi CSV uses 'id' not 'qId', 'correct' is number not letter
    results = []
    total = len(rows)

    for i, row in enumerate(rows):
        qid_raw = row.get("id", "")
        # Convert R5-午前-01 -> R5-AM-01
        qid = qid_raw.replace("午前", "AM").replace("午後", "PM")
        kid = archi_qid_to_kid(qid)
        qb_correct_num = row.get("correct", "")

        if kid is None:
            results.append({"qId": qid_raw, "status": "SKIP", "detail": "no_id_map"})
            continue

        print(f"\r[{i+1}/{total}] {qid_raw} (ID={kid})", end="", flush=True)

        fetched = fetch_answer_and_explanation(ARCHI_BASE, kid)

        if fetched["error"]:
            results.append({"qId": qid_raw, "status": "ERR", "detail": fetched["error"]})
        else:
            km_correct_num = fetched["correct"]
            km_str = str(km_correct_num) if km_correct_num else "?"
            qb_str = str(qb_correct_num).strip()

            # Handle multi-answer (e.g. "2,4" or "BD")
            if km_str == qb_str:
                status = "OK"
            else:
                status = "NG"

            results.append({
                "qId": qid_raw,
                "status": status,
                "qb_correct": qb_str,
                "km_correct": km_str,
                "km_expl_preview": (fetched["explanation"] or "")[:50],
            })

        time.sleep(SLEEP_SEC)

    print()
    return results


# -------------------------------------------------------------------
# レポート出力
# -------------------------------------------------------------------
def write_report(results: list[dict], label: str) -> str:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(REPORT_DIR, f"kakomonn_verify_{label}_{ts}.txt")

    ok = sum(1 for r in results if r["status"] == "OK")
    ng = sum(1 for r in results if r["status"] == "NG")
    err = sum(1 for r in results if r["status"] == "ERR")
    skip = sum(1 for r in results if r["status"] == "SKIP")

    lines = []
    lines.append(f"=== kakomonn.com 照合レポート: {label} ===")
    lines.append(f"実行日時: {datetime.now().isoformat()}")
    lines.append(f"OK: {ok}, NG: {ng}, ERR: {err}, SKIP: {skip} / {len(results)}")
    lines.append("")

    # NG details
    ng_items = [r for r in results if r["status"] == "NG"]
    if ng_items:
        lines.append(f"--- NG ({len(ng_items)}問) ---")
        for r in ng_items:
            lines.append(f"  {r['qId']}: km={r.get('km_correct','?')} QB={r.get('qb_correct','?')}")
        lines.append("")

    # ERR details
    err_items = [r for r in results if r["status"] == "ERR"]
    if err_items:
        lines.append(f"--- ERR ({len(err_items)}問) ---")
        for r in err_items:
            lines.append(f"  {r['qId']}: {r.get('detail','')}")
        lines.append("")

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return path


# -------------------------------------------------------------------
# メイン
# -------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="kakomonn.com 全問照合 v3")
    parser.add_argument("--verify", action="store_true", help="全問照合（CSV変更なし）")
    parser.add_argument("--archi", action="store_true", help="建築も照合")
    parser.add_argument("--dry-run", action="store_true", help="IDマッピング確認のみ")
    args = parser.parse_args()

    os.makedirs(REPORT_DIR, exist_ok=True)

    if args.dry_run:
        # Dry run: show ID mapping for first/last of each segment
        print("=== 土木 IDマッピング ===")
        with open(DOBOKU_CSV, encoding=ENCODING) as f:
            for row in csv.DictReader(f):
                qid = row.get("qId", "")
                kid = doboku_qid_to_kid(qid)
                if qid.endswith("-001") or qid.endswith("-035") or qid.endswith("-061") or qid.endswith("-066"):
                    print(f"  {qid} -> {kid}")
        return

    if args.verify:
        print("=== 土木 全問照合 ===")
        doboku_results = verify_doboku(DOBOKU_CSV)
        path = write_report(doboku_results, "doboku")
        ok = sum(1 for r in doboku_results if r["status"] == "OK")
        ng = sum(1 for r in doboku_results if r["status"] == "NG")
        err = sum(1 for r in doboku_results if r["status"] == "ERR")
        print(f"\n土木: OK={ok}, NG={ng}, ERR={err} / {len(doboku_results)}")
        print(f"レポート: {path}")

        if args.archi:
            print("\n=== 建築 全問照合 ===")
            archi_results = verify_archi(ARCHI_CSV)
            path2 = write_report(archi_results, "archi")
            ok2 = sum(1 for r in archi_results if r["status"] == "OK")
            ng2 = sum(1 for r in archi_results if r["status"] == "NG")
            err2 = sum(1 for r in archi_results if r["status"] == "ERR")
            print(f"\n建築: OK={ok2}, NG={ng2}, ERR={err2} / {len(archi_results)}")
            print(f"レポート: {path2}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
