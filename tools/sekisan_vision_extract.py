#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import json
import time
from pathlib import Path
from typing import Iterable

import fitz
from openai import OpenAI
from pydantic import BaseModel, Field


BASE_DIR = Path(r"C:/tmp/kakomon/sekisanshi")
API_KEY_PATH = Path(r"C:/ProgramData/RK10/credentials/openai_api_key.txt")
DEFAULT_OUTPUT = BASE_DIR / "sekisan_vision_gpt54.jsonl"
DEFAULT_MODEL = "gpt-5.4"
DEFAULT_SCALE = 3

PDFS = {
    "H25": "sekisan_H25_1ji.pdf",
    "H26": "sekisan_H26_1ji.pdf",
    "H27": "sekisan_H27_1ji.pdf",
    "H28": "sekisan_H28_1ji.pdf",
    "H29": "sekisan_H29_1ji.pdf",
    "H30": "sekisan_H30_1ji.pdf",
    "R1": "sekisan_R1_1ji.pdf",
    "R2": "sekisan_R2_1ji.pdf",
    "R3": "sekisan_R3_1ji.pdf",
    "R4": "sekisan_R4_1ji.pdf",
    "R5": "sekisan_R5_1ji.pdf",
    "R6": "sekisan_R6_1ji.pdf",
    "R7": "sekisan_R7_1ji.pdf",
}

YEAR_ORDER = ["H25", "H26", "H27", "H28", "H29", "H30", "R1", "R2", "R3", "R4", "R5", "R6", "R7"]
LETTER_MAP = {"1": "A", "2": "B", "3": "C", "4": "D", "A": "A", "B": "B", "C": "C", "D": "D"}

SYSTEM_PROMPT = """あなたは建築積算士試験問題の高精度な構造化抽出器です。

目的:
- 1ページ=1問の試験ページ画像から、設問・4択・正答・解説を正確に抽出する
- JSONスキーマに厳密に従う

重要ルール:
- question_number は画像内の問題番号をそのまま返す（例: Ⅰ-1, II-11）
- stem には設問文全文を入れる
- 「最も不適切なものはどれか。」「最も適切なものはどれか。」等の指示文を含める
- 図や表がある場合でも、stem 内の図参照文（例: 下図の〜）は含める
- choiceA-D には各選択肢本文のみを入れる
- 正答は右上の正答肢番号 1-4 を A-D に変換して返す
- 解説は「解説」「【解説】」「解 説」欄の本文を explainShort にまとめる
- 出典、整理番号、章目、ページ番号、ラベル名などのメタ情報は含めない
- 数値・記号・単位は原文どおりを優先する
- 判別が難しい文字でも、空欄にはせず、最善の読みを返す
- 複数正解が明示されていない限り correct は A/B/C/D のいずれか1つ
"""

USER_PROMPT_TEMPLATE = """この画像は建築積算士試験の1ページです。
年度: {year}
ページ番号: {page}

次の項目を抽出してください。
- 問題番号
- 設問文
- 選択肢A-D
- 正答
- 解説

図表の内容説明は不要です。JSONスキーマに厳密に従ってください。"""


class VisionExtraction(BaseModel):
    question_number: str = Field(description="問題番号。例: Ⅰ-1, II-11")
    stem: str = Field(description="設問文全文")
    choiceA: str
    choiceB: str
    choiceC: str
    choiceD: str
    correct: str = Field(description="A/B/C/D")
    explainShort: str = Field(description="解説欄の本文")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract structured exam data from sekisan PDFs with GPT-5.4 Vision.")
    parser.add_argument("--qids", help="Comma-separated qIds like H26sekisan-040,R4sekisan-035")
    parser.add_argument("--years", help="Comma-separated years like H25,H26,R4")
    parser.add_argument("--page-range", default="1-50", help="Inclusive page range for --years, e.g. 1-50 or 35-40")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--scale", type=int, default=DEFAULT_SCALE)
    parser.add_argument("--sleep", type=float, default=0.5, help="Sleep between requests in seconds")
    parser.add_argument("--max-output-tokens", type=int, default=1400)
    parser.add_argument("--retries", type=int, default=3, help="Retry count per page")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--force", action="store_true", help="Re-run even if qId already exists in output jsonl")
    return parser.parse_args()


def normalize_correct(value: str) -> str:
    token = (value or "").strip().upper()
    return LETTER_MAP.get(token, token)


def year_sort_key(year: str) -> tuple[int, int]:
    return (0, YEAR_ORDER.index(year))


def parse_qid(qid: str) -> tuple[str, int]:
    year, page = qid.split("sekisan-")
    return year, int(page)


def parse_page_range(raw: str) -> list[int]:
    start_raw, end_raw = raw.split("-", 1)
    start = int(start_raw)
    end = int(end_raw)
    if start > end:
        start, end = end, start
    return list(range(start, end + 1))


def build_targets(args: argparse.Namespace) -> list[tuple[str, int]]:
    targets: list[tuple[str, int]] = []
    if args.qids:
        for qid in args.qids.split(","):
            qid = qid.strip()
            if not qid:
                continue
            targets.append(parse_qid(qid))
    if args.years:
        pages = parse_page_range(args.page_range)
        for year in [y.strip() for y in args.years.split(",") if y.strip()]:
            for page in pages:
                targets.append((year, page))
    deduped = sorted(set(targets), key=lambda item: (year_sort_key(item[0]), item[1]))
    if not deduped:
        raise SystemExit("No targets specified. Use --qids or --years.")
    return deduped


def load_existing(output_path: Path) -> dict[str, dict]:
    existing: dict[str, dict] = {}
    if not output_path.exists():
        return existing
    with output_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            existing[row["qId"]] = row
    return existing


def load_client() -> OpenAI:
    api_key = API_KEY_PATH.read_text(encoding="utf-8").strip()
    if not api_key:
        raise RuntimeError(f"OpenAI API key file is empty: {API_KEY_PATH}")
    return OpenAI(api_key=api_key)


def render_page_as_data_url(pdf_path: Path, page_number: int, scale: int) -> str:
    with fitz.open(pdf_path) as doc:
        page = doc[page_number - 1]
        pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale))
        png_bytes = pix.tobytes("png")
    encoded = base64.b64encode(png_bytes).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def extract_single(
    client: OpenAI,
    *,
    model: str,
    year: str,
    page: int,
    image_data_url: str,
    max_output_tokens: int,
) -> tuple[VisionExtraction, object]:
    response = client.responses.parse(
        model=model,
        instructions=SYSTEM_PROMPT,
        reasoning={"effort": "low"},
        max_output_tokens=max_output_tokens,
        text={"verbosity": "low"},
        input=[
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": USER_PROMPT_TEMPLATE.format(year=year, page=page)},
                    {"type": "input_image", "image_url": image_data_url},
                ],
            }
        ],
        text_format=VisionExtraction,
    )
    return response.output_parsed, response


def iter_results(args: argparse.Namespace, targets: Iterable[tuple[str, int]], output_path: Path) -> None:
    client = load_client()
    existing = load_existing(output_path)

    with output_path.open("a", encoding="utf-8") as sink:
        for year, page in targets:
            qid = f"{year}sekisan-{page:03d}"
            if qid in existing and not args.force:
                print(f"SKIP {qid}: already extracted")
                continue

            pdf_name = PDFS.get(year)
            if not pdf_name:
                print(f"SKIP {qid}: no PDF mapping for {year}")
                continue

            pdf_path = BASE_DIR / pdf_name
            if not pdf_path.exists():
                print(f"SKIP {qid}: missing PDF {pdf_path}")
                continue

            print(f"RUN  {qid} -> {args.model}")
            image_data_url = render_page_as_data_url(pdf_path, page, args.scale)
            parsed = None
            response = None
            for attempt in range(1, args.retries + 1):
                try:
                    parsed, response = extract_single(
                        client,
                        model=args.model,
                        year=year,
                        page=page,
                        image_data_url=image_data_url,
                        max_output_tokens=args.max_output_tokens,
                    )
                    break
                except Exception as exc:  # noqa: BLE001
                    print(f"ERR  {qid}: attempt {attempt}/{args.retries} -> {exc}")
                    if attempt == args.retries:
                        parsed = None
                        response = None
                    else:
                        time.sleep(max(args.sleep, 1.0) * attempt)

            if parsed is None:
                print(f"FAIL {qid}: exhausted retries")
                continue

            record = parsed.model_dump()
            record["correct"] = normalize_correct(record.get("correct", ""))
            record["qId"] = qid
            record["year"] = year
            record["page"] = page
            record["model"] = args.model
            record["response_id"] = getattr(response, "id", "")
            sink.write(json.dumps(record, ensure_ascii=False) + "\n")
            sink.flush()
            print(f"DONE {qid}: correct={record['correct']} question_number={record['question_number']}")
            time.sleep(args.sleep)


def main() -> None:
    args = parse_args()
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    targets = build_targets(args)
    iter_results(args, targets, output_path)


if __name__ == "__main__":
    main()
