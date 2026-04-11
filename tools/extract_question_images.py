"""
Extract per-question images from exam PDFs (doboku-14w).

This script detects question boundaries by finding "No." labels in PDF text,
then crops each question region and saves it as a PNG.

Naming convention:
  qId:       R7gakkaA-001
  file name: R7gakkaA_001.png  (qId with '-' replaced by '_')

Usage:
  python extract_question_images.py --pdf "C:/path/R7gakkaA_mondai.pdf" --segment-id R7gakkaA

Optional:
  --only "1-5,10,12"
  --scale 2.0
  --out-dir "C:/.../docs/assets/doboku-14w/images"
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple

import fitz  # PyMuPDF
from PIL import Image


START_WORD_X0_MAX = 140.0
# Keep question header visible but avoid grabbing previous paragraph.
TOP_PAD_PTS = 0.0
BOTTOM_PAD_PTS = 6.0
# Strip page footer area (page number like "― 1 ―" tends to sit near bottom).
BOTTOM_CUTOFF_PTS = 60.0


def _default_out_dir() -> Path:
    tools_dir = Path(__file__).resolve().parent
    github_root = tools_dir.parent.parent  # .../Github
    return (
        github_root
        / "PDF-RakuRaku-Seisan"
        / "docs"
        / "assets"
        / "doboku-14w"
        / "images"
    )


def _parse_only(only: str) -> Set[int]:
    out: Set[int] = set()
    raw = (only or "").strip()
    if not raw:
        return out
    for part in raw.split(","):
        p = part.strip()
        if not p:
            continue
        if "-" in p:
            a, b = p.split("-", 1)
            a = a.strip()
            b = b.strip()
            if not a or not b:
                raise ValueError(f"Invalid --only range: {p!r}")
            start = int(a)
            end = int(b)
            if end < start:
                start, end = end, start
            for n in range(start, end + 1):
                out.add(n)
        else:
            out.add(int(p))
    return out


def _find_question_starts_on_page(page: fitz.Page) -> List[Tuple[int, float]]:
    """
    Return question starts on this page as (q_num, y0).

    Heuristic:
      - word starts with "【No." (question header; avoids false-positives like "No. 1～No.5")
      - word x0 is near left margin
      - next word contains digits (e.g., "12】")
    """
    words = page.get_text("words")  # (x0,y0,x1,y1,text,block,line,word_no)
    words_sorted = sorted(words, key=lambda w: (w[1], w[0]))

    found: Dict[int, float] = {}
    for i, w in enumerate(words_sorted[:-1]):
        txt = str(w[4] or "")
        if not txt.startswith("【No."):
            continue
        x0 = float(w[0])
        if x0 > START_WORD_X0_MAX:
            continue

        nxt = str(words_sorted[i + 1][4] or "")
        m = re.search(r"(\d{1,3})", nxt)
        if not m:
            continue
        q_num = int(m.group(1))
        y0 = float(w[1])
        if q_num <= 0 or q_num > 999:
            continue

        # Deduplicate (keep the top-most y0 if multiple)
        if q_num not in found or y0 < found[q_num]:
            found[q_num] = y0

    return sorted(found.items(), key=lambda t: t[1])


def _collect_start_positions(doc: fitz.Document) -> Dict[int, Tuple[int, float]]:
    pos: Dict[int, Tuple[int, float]] = {}
    for page_index in range(doc.page_count):
        page = doc[page_index]
        starts = _find_question_starts_on_page(page)
        for q_num, y0 in starts:
            if q_num in pos:
                # Keep the earliest occurrence (should not happen in normal PDFs).
                continue
            pos[q_num] = (page_index, y0)
    return pos


def _render_clip(
    page: fitz.Page,
    rect: fitz.Rect,
    scale: float,
) -> Image.Image:
    mat = fitz.Matrix(scale, scale)
    pix = page.get_pixmap(matrix=mat, clip=rect, alpha=False)
    return Image.frombytes("RGB", (pix.width, pix.height), pix.samples)


def _stitch_vertical(images: Sequence[Image.Image]) -> Image.Image:
    if len(images) == 1:
        return images[0]
    max_w = max(im.width for im in images)
    total_h = sum(im.height for im in images)
    out = Image.new("RGB", (max_w, total_h), (255, 255, 255))
    y = 0
    for im in images:
        out.paste(im, (0, y))
        y += im.height
    return out


def extract_question_images(
    pdf_path: Path,
    segment_id: str,
    out_dir: Path,
    scale: float,
    only: Optional[Set[int]] = None,
    limit: int = 0,
) -> List[Path]:
    only = only or set()
    out_dir.mkdir(parents=True, exist_ok=True)

    doc = fitz.open(str(pdf_path))
    starts = _collect_start_positions(doc)
    if not starts:
        raise RuntimeError("No question starts detected. Check PDF text extraction.")

    q_nums = sorted(starts.keys())
    written: List[Path] = []

    for idx, q_num in enumerate(q_nums):
        if only and q_num not in only:
            continue
        if limit and len(written) >= limit:
            break

        start_page, start_y0 = starts[q_num]
        if idx + 1 < len(q_nums):
            next_q = q_nums[idx + 1]
            end_page, end_y0 = starts[next_q]
        else:
            end_page, end_y0 = doc.page_count - 1, float(doc[doc.page_count - 1].rect.height)

        clips: List[Tuple[int, fitz.Rect]] = []
        for pi in range(start_page, end_page + 1):
            page = doc[pi]
            w = float(page.rect.width)
            h = float(page.rect.height)

            if pi == start_page:
                y0 = max(0.0, float(start_y0) - TOP_PAD_PTS)
            else:
                y0 = 0.0

            if pi == end_page:
                y1 = float(end_y0) - BOTTOM_PAD_PTS
            else:
                y1 = h

            y1 = min(y1, h - BOTTOM_CUTOFF_PTS)
            if y1 <= y0 + 4:
                continue

            clips.append((pi, fitz.Rect(0.0, y0, w, y1)))

        if not clips:
            continue

        parts: List[Image.Image] = []
        for pi, rect in clips:
            parts.append(_render_clip(doc[pi], rect, scale))

        stitched = _stitch_vertical(parts)

        q_id = f"{segment_id}-{q_num:03d}"
        file_base = q_id.replace("-", "_")
        out_path = out_dir / f"{file_base}.png"
        stitched.save(out_path, format="PNG", optimize=True)
        written.append(out_path)

    return written


def main() -> None:
    ap = argparse.ArgumentParser(description="Extract per-question PNG images from PDF")
    ap.add_argument("--pdf", required=True, help="Input PDF file path")
    ap.add_argument("--segment-id", required=True, help="Segment ID (e.g., R7gakkaA)")
    ap.add_argument("--out-dir", default=str(_default_out_dir()), help="Output directory")
    ap.add_argument("--scale", type=float, default=2.0, help="Render scale (2.0 ~= 144dpi)")
    ap.add_argument("--only", default="", help='Only these question numbers, e.g. "1-5,10,12"')
    ap.add_argument("--limit", type=int, default=0, help="Max number of images to write (0 = no limit)")
    args = ap.parse_args()

    pdf_path = Path(args.pdf)
    if not pdf_path.exists():
        raise SystemExit(f"PDF not found: {pdf_path}")

    out_dir = Path(args.out_dir)
    only = _parse_only(args.only)

    written = extract_question_images(
        pdf_path=pdf_path,
        segment_id=str(args.segment_id),
        out_dir=out_dir,
        scale=float(args.scale),
        only=only,
        limit=int(args.limit),
    )

    print(f"Saved images: {len(written)}")
    if written:
        print(f"First: {written[0]}")
        print(f"Out dir: {out_dir}")


if __name__ == "__main__":
    main()
