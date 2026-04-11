"""
scrape_kakomonn.py
kakomonn.com から 1級土木施工管理技士の選択肢解説文を取得し、CSVに統合する。

使用方法:
  python scrape_kakomonn.py --dry-run   # IDマッピング確認のみ（通信なし）
  python scrape_kakomonn.py             # 本番実行
"""

import argparse
import csv
import os
import re
import shutil
import sys
import time
from datetime import datetime

import requests
from bs4 import BeautifulSoup

# -------------------------------------------------------------------
# 設定
# -------------------------------------------------------------------
CSV_PATH = r"C:\ProgramData\Generative AI\Github\doboku-14w-training\tools\questionbank_drive_import.csv"
ENCODING = "utf-8-sig"
SLEEP_SEC = 1.0
BASE_URL = "https://1dobokusekou.kakomonn.com/questions/{id}"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

# IDマッピング: prefix -> base_id
ID_MAP = {
    "R1gakkaA": 47838,
    "R1gakkaB": 47899,
    "R2gakkaA": 53624,
    "R2gakkaB": 53685,
    "R3gakkaA": 58752,
    "R3gakkaB": 58813,
}


# -------------------------------------------------------------------
# IDマッピング関数
# -------------------------------------------------------------------
def qid_to_kakomonn_id(qid: str) -> int | None:
    """
    qId (例: R2gakkaA-033) を kakomonn の問題ID に変換する。
    マッピング対象外の場合は None を返す。
    """
    for prefix, base in ID_MAP.items():
        if qid.startswith(prefix + "-"):
            suffix = qid[len(prefix) + 1:]
            try:
                n = int(suffix)
                return base + n
            except ValueError:
                return None
    return None


# -------------------------------------------------------------------
# スクレイピング関数
# -------------------------------------------------------------------
def fetch_explanations(kakomonn_id: int) -> dict | None:
    """
    指定 ID のページから選択肢解説を取得する。
    取得失敗時は None を返す。
    """
    url = BASE_URL.format(id=kakomonn_id)
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        resp.encoding = "utf-8"
    except requests.RequestException as e:
        print(f"  [ERROR] HTTP 取得失敗: {url} -> {e}")
        return None

    soup = BeautifulSoup(resp.text, "html.parser")

    # .sect_commentary .item .text .expound-txt を探す
    expound_div = soup.select_one(".sect_commentary .item .text .expound-txt")
    if expound_div is None:
        # フォールバック: .expound-txt のみで検索
        expound_div = soup.select_one(".expound-txt")

    if expound_div is None:
        print(f"  [WARN] .expound-txt が見つかりません: {url}")
        return None

    # <p> タグを連結してテキストを取得
    paragraphs = [p.get_text(strip=True) for p in expound_div.find_all("p") if p.get_text(strip=True)]
    full_text = "\n".join(paragraphs)

    if not full_text:
        print(f"  [WARN] テキストが空です: {url}")
        return None

    return parse_explanations(full_text)


# -------------------------------------------------------------------
# テキスト解析関数
# -------------------------------------------------------------------
# 選択肢の見出しパターン（全角・半角両対応）
CHOICE_PATTERN = re.compile(r"(?:^|\n)([１1２2３3４4][\．\.])")


def parse_explanations(text: str) -> dict:
    """
    解説テキストを explainA/B/C/D と explainShort に分割する。
    """
    # 選択肢の開始位置を検出
    splits = []
    for m in re.finditer(r"[１1２2３3４4][\．\.]", text):
        splits.append((m.start(), m.group(0)))

    if not splits:
        # 分割できない場合は全体を explainA に入れる
        short = text[:200] if len(text) > 200 else text
        return {
            "explainA": text,
            "explainB": "",
            "explainC": "",
            "explainD": "",
            "explainShort": short,
        }

    sections = []
    for i, (pos, marker) in enumerate(splits):
        end = splits[i + 1][0] if i + 1 < len(splits) else len(text)
        section_text = text[pos:end].strip()
        sections.append(section_text)

    # 最大4つに制限
    sections = sections[:4]

    keys = ["explainA", "explainB", "explainC", "explainD"]
    result = {k: "" for k in keys}
    for i, sec in enumerate(sections):
        result[keys[i]] = sec

    # explainShort: 全体テキストの先頭200文字
    short = text.replace("\n", " ")
    result["explainShort"] = short[:200] if len(short) > 200 else short

    return result


# -------------------------------------------------------------------
# CSV 処理
# -------------------------------------------------------------------
def load_csv(path: str) -> tuple[list[dict], list[str]]:
    """CSVを読み込み (rows, fieldnames) を返す。"""
    with open(path, encoding=ENCODING, newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []
        rows = list(reader)
    return rows, fieldnames


def save_csv(path: str, rows: list[dict], fieldnames: list[str]) -> None:
    """CSVに書き込む。"""
    with open(path, "w", encoding=ENCODING, newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def backup_csv(path: str) -> str:
    """タイムスタンプ付きバックアップを作成し、バックアップパスを返す。"""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    base, ext = os.path.splitext(path)
    backup_path = f"{base}_backup_{ts}{ext}"
    shutil.copy2(path, backup_path)
    return backup_path


# -------------------------------------------------------------------
# メイン処理
# -------------------------------------------------------------------
def run_dry(rows: list[dict]) -> None:
    """dry-run: IDマッピング確認のみ（最初の10件を表示）。"""
    targets = [r for r in rows if r["qId"].startswith(("R1", "R2", "R3")) and not r.get("explainA", "").strip()]
    print(f"[DRY-RUN] スクレイピング対象: {len(targets)} 件")
    print(f"{'qId':<20} {'kakomonn_id':>12}  {'URL'}")
    print("-" * 80)
    for r in targets[:10]:
        qid = r["qId"]
        kid = qid_to_kakomonn_id(qid)
        if kid:
            url = BASE_URL.format(id=kid)
        else:
            url = "(マッピング対象外)"
        print(f"{qid:<20} {str(kid) if kid else 'N/A':>12}  {url}")
    if len(targets) > 10:
        print(f"  ... 他 {len(targets) - 10} 件")


def run_scrape(rows: list[dict], fieldnames: list[str]) -> None:
    """本番実行: スクレイピングして CSV を更新。"""
    targets = [
        (i, r) for i, r in enumerate(rows)
        if r["qId"].startswith(("R1", "R2", "R3")) and not r.get("explainA", "").strip()
    ]
    total = len(targets)
    print(f"スクレイピング対象: {total} 件")

    if total == 0:
        print("対象なし。終了します。")
        return

    # バックアップ
    backup_path = backup_csv(CSV_PATH)
    print(f"バックアップ作成: {backup_path}")
    print()

    count_ok = 0
    count_skip = 0
    count_err = 0

    for seq, (row_idx, row) in enumerate(targets, start=1):
        qid = row["qId"]
        kid = qid_to_kakomonn_id(qid)

        if kid is None:
            print(f"[{seq:3d}/{total}] SKIP  {qid} (IDマッピング対象外)")
            count_skip += 1
            continue

        url = BASE_URL.format(id=kid)
        print(f"[{seq:3d}/{total}] 処理中 {qid} (ID={kid}) ...", end=" ", flush=True)

        result = fetch_explanations(kid)

        if result is None:
            print("ERROR - スキップ")
            count_err += 1
        else:
            rows[row_idx]["explainA"] = result["explainA"]
            rows[row_idx]["explainB"] = result["explainB"]
            rows[row_idx]["explainC"] = result["explainC"]
            rows[row_idx]["explainD"] = result["explainD"]
            if result.get("explainShort"):
                rows[row_idx]["explainShort"] = result["explainShort"]
            print(f"OK  (explainA={result['explainA'][:40]!r}...)")
            count_ok += 1
            # 進捗保存（10件ごと）
            if seq % 10 == 0:
                save_csv(CSV_PATH, rows, fieldnames)
                print(f"  >>> 中間保存 ({seq}/{total})")

        time.sleep(SLEEP_SEC)

    # 最終保存
    save_csv(CSV_PATH, rows, fieldnames)

    print()
    print("=" * 60)
    print(f"完了サマリー")
    print(f"  対象合計 : {total} 件")
    print(f"  成功     : {count_ok} 件")
    print(f"  スキップ : {count_skip} 件")
    print(f"  エラー   : {count_err} 件")
    print(f"  CSV保存  : {CSV_PATH}")
    print("=" * 60)


# -------------------------------------------------------------------
# エントリーポイント
# -------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(description="kakomonn.com スクレイパー (1級土木)")
    parser.add_argument("--dry-run", action="store_true", help="IDマッピング確認のみ（通信なし）")
    args = parser.parse_args()

    rows, fieldnames = load_csv(CSV_PATH)

    if args.dry_run:
        run_dry(rows)
    else:
        run_scrape(rows, fieldnames)


if __name__ == "__main__":
    main()
