"""
Extract per-question *figure/table only* images from exam PDFs (doboku-14w).

We detect question boundaries by finding a "【No." label in PDF text, then within each question
region we detect a likely figure/table region using:
  - vector drawings (page.get_drawings()) bounding boxes
  - raster images (page.get_images(full=True)) bounding boxes (if any)

Heuristics to reduce false positives:
  - Prefer graphics above the first choice marker (e.g. "(1)", "⑴", "①").
  - Require minimum bbox width/height and minimum area ratio vs. the search region.
  - Expand bbox with nearby text so labels inside figures are not cut off.

Naming convention:
  qId:       R7gakkaA-001
  file name: R7gakkaA_001.png  (qId with '-' replaced by '_')

Usage:
  python extract_question_figures.py --pdf "C:/path/R7gakkaA_mondai.pdf" --segment-id R7gakkaA

Optional:
  --only "1-5,10,12"
  --scale 2.0
  --out-dir "C:/.../docs/assets/doboku-14w/figures"
  --min-ratio 0.04 --min-width-pts 80 --min-height-pts 60
  --cluster-pad-pts 40 --text-pad-pts 10

Outputs:
  - PNG files (only for questions where a figure/table was detected)
  - figures_manifest.csv (qId, pageIndex, ratio, bbox, etc.)
"""

from __future__ import annotations

import argparse
import csv
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple

import fitz  # PyMuPDF
from PIL import Image


# Question header prefix: "【No." (U+3010 is '【')
Q_START_PREFIX = "\u3010No."
START_WORD_X0_MAX_PTS = 140.0

# Keep the question header visible but strip page footer area (page number).
TOP_PAD_PTS = 0.0
BOTTOM_PAD_PTS = 6.0
BOTTOM_CUTOFF_PTS = 60.0


# Choice marker tokens commonly used in the PDFs.
# - "(1)" or "（1）"
# - "①" (circled digits: U+2460..U+2473)
# - "⑴" (parenthesized digits: U+2474..U+2487)
CHOICE_MARKER_RE = re.compile(
    r"^(?:"
    r"\(\d{1,2}\)|\uFF08\d{1,2}\uFF09|"
    r"[\u2460-\u2473]|[\u2474-\u2487]|"
    r"\d{1,2}\)|\d{1,2}[.)]"
    r")"
)

# Answer choice markers are usually near the left margin. This reduces false
# positives from "(1)～(4)" labels inside figures.
CHOICE_MARKER_X0_MAX_PTS = 140.0


@dataclass(frozen=True)
class FigureCandidate:
    page_index: int
    ratio: float
    clip_rect: fitz.Rect
    search_rect: fitz.Rect
    bbox: fitz.Rect
    choice_y: Optional[float]


def _default_out_dir() -> Path:
    tools_dir = Path(__file__).resolve().parent
    github_root = tools_dir.parent.parent  # .../Github
    return (
        github_root
        / "PDF-RakuRaku-Seisan"
        / "docs"
        / "assets"
        / "doboku-14w"
        / "figures"
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
      - word starts with "【No."
      - word x0 is near left margin
      - next word contains digits (e.g., "12】")
    """
    words = page.get_text("words")  # (x0,y0,x1,y1,text,block,line,word_no)
    words_sorted = sorted(words, key=lambda w: (w[1], w[0]))

    found: Dict[int, float] = {}
    for i, w in enumerate(words_sorted[:-1]):
        txt = str(w[4] or "")
        if not txt.startswith(Q_START_PREFIX):
            continue
        x0 = float(w[0])
        if x0 > START_WORD_X0_MAX_PTS:
            continue

        nxt = str(words_sorted[i + 1][4] or "")
        m = re.search(r"(\d{1,3})", nxt)
        if not m:
            continue
        q_num = int(m.group(1))
        y0 = float(w[1])
        if q_num <= 0 or q_num > 999:
            continue
        if q_num not in found or y0 < found[q_num]:
            found[q_num] = y0

    return sorted(found.items(), key=lambda t: t[1])


def _collect_start_positions(doc: fitz.Document) -> Dict[int, Tuple[int, float]]:
    pos: Dict[int, Tuple[int, float]] = {}
    for page_index in range(doc.page_count):
        page = doc[page_index]
        for q_num, y0 in _find_question_starts_on_page(page):
            if q_num in pos:
                continue
            pos[q_num] = (page_index, y0)
    return pos


def _intersect(a: fitz.Rect, b: fitz.Rect) -> Optional[fitz.Rect]:
    x0 = max(a.x0, b.x0)
    y0 = max(a.y0, b.y0)
    x1 = min(a.x1, b.x1)
    y1 = min(a.y1, b.y1)
    if x1 <= x0 or y1 <= y0:
        return None
    return fitz.Rect(x0, y0, x1, y1)


def _cluster_union(rects: Sequence[fitz.Rect], pad_pts: float) -> List[fitz.Rect]:
    """
    Merge rectangles into clusters by proximity / overlap.
    pad_pts controls how aggressively nearby elements get merged.
    """
    clusters: List[fitz.Rect] = []
    for r in rects:
        merged = False
        for i, c in enumerate(clusters):
            if fitz.Rect(c.x0 - pad_pts, c.y0 - pad_pts, c.x1 + pad_pts, c.y1 + pad_pts).intersects(r):
                clusters[i] = c | r
                merged = True
                break
        if not merged:
            clusters.append(r)

    changed = True
    while changed:
        changed = False
        new: List[fitz.Rect] = []
        for r in clusters:
            merged = False
            for i, c in enumerate(new):
                if fitz.Rect(c.x0 - pad_pts, c.y0 - pad_pts, c.x1 + pad_pts, c.y1 + pad_pts).intersects(r):
                    new[i] = c | r
                    merged = True
                    changed = True
                    break
            if not merged:
                new.append(r)
        clusters = new
    return clusters


def _find_choice_y0(page: fitz.Page, clip: fitz.Rect) -> Optional[float]:
    words = page.get_text("words")
    y: Optional[float] = None
    for w in words:
        wx0 = float(w[0])
        wy0 = float(w[1])
        if wy0 < clip.y0 or wy0 > clip.y1:
            continue
        if wx0 > CHOICE_MARKER_X0_MAX_PTS:
            continue
        t = str(w[4] or "").strip()
        if not t:
            continue
        if CHOICE_MARKER_RE.match(t):
            if y is None or wy0 < y:
                y = wy0
    return y


def _has_significant_graphics_below_y(
    page: fitz.Page,
    clip: fitz.Rect,
    y0: float,
    *,
    cluster_pad_pts: float,
    min_width_pts: float,
    min_height_pts: float,
    min_ratio: float,
    min_graphic_area_pts2: float,
) -> bool:
    """
    Safeguard for cases where (1)-(4) markers are inside the figure itself.

    Example: "下図に示す(1)～(4)" where (1)-(4) labels are placed next to images.
    If we treat the first "(1)" as the start of answer choices, we would clip away
    the figure. When the region below the marker still contains a large graphic
    cluster, we assume the marker is part of the figure and do not truncate.
    """
    below = fitz.Rect(float(clip.x0), float(y0) + 1.0, float(clip.x1), float(clip.y1))
    if below.y1 <= below.y0 + 4.0 or below.get_area() <= 0:
        return False

    rects = _collect_graphic_rects(page, below, min_area_pts2=float(min_graphic_area_pts2))
    if not rects:
        return False

    clusters = _cluster_union(rects, pad_pts=float(cluster_pad_pts))
    area_total = float(below.get_area())
    for r in clusters:
        if (r.x1 - r.x0) < float(min_width_pts) or (r.y1 - r.y0) < float(min_height_pts):
            continue
        ratio = float(r.get_area()) / area_total if area_total > 0 else 0.0
        if ratio >= float(min_ratio):
            return True

    return False


def _collect_graphic_rects(
    page: fitz.Page,
    search: fitz.Rect,
    *,
    min_area_pts2: float,
) -> List[fitz.Rect]:
    W = float(page.rect.width)
    H = float(page.rect.height)

    rects: List[fitz.Rect] = []

    # Raster images (if any)
    try:
        imgs = page.get_images(full=True)
    except Exception:
        imgs = []
    for tup in imgs:
        xref = tup[0]
        try:
            irs = page.get_image_rects(xref)
        except Exception:
            continue
        for r in irs:
            pr = fitz.Rect(max(0.0, r.x0), max(0.0, r.y0), min(W, r.x1), min(H, r.y1))
            inter = _intersect(pr, search)
            if not inter:
                continue
            if inter.get_area() >= min_area_pts2:
                rects.append(inter)

    # Vector drawings
    for d in page.get_drawings():
        r = d.get("rect")
        if not r:
            continue
        pr = fitz.Rect(max(0.0, r.x0), max(0.0, r.y0), min(W, r.x1), min(H, r.y1))
        inter = _intersect(pr, search)
        if not inter:
            continue
        if inter.get_area() >= min_area_pts2:
            rects.append(inter)

    return rects


def _expand_bbox_with_nearby_text(
    page: fitz.Page,
    bbox: fitz.Rect,
    search: fitz.Rect,
    *,
    text_pad_pts: float,
) -> fitz.Rect:
    expanded = fitz.Rect(bbox.x0 - text_pad_pts, bbox.y0 - text_pad_pts, bbox.x1 + text_pad_pts, bbox.y1 + text_pad_pts)
    words = page.get_text("words")
    out = fitz.Rect(bbox)
    for w in words:
        x0, y0, x1, y1 = map(float, w[:4])
        wr = fitz.Rect(x0, y0, x1, y1)
        if not wr.intersects(search):
            continue
        if wr.intersects(expanded):
            out = out | wr
    # Clamp to page bounds
    W = float(page.rect.width)
    H = float(page.rect.height)
    out = fitz.Rect(max(0.0, out.x0), max(0.0, out.y0), min(W, out.x1), min(H, out.y1))
    return out


def _render_clip(page: fitz.Page, rect: fitz.Rect, scale: float) -> Image.Image:
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


def _best_figure_candidate_on_page(
    page: fitz.Page,
    clip: fitz.Rect,
    *,
    min_ratio: float,
    min_width_pts: float,
    min_height_pts: float,
    cluster_pad_pts: float,
    text_pad_pts: float,
    min_graphic_area_pts2: float,
) -> Optional[FigureCandidate]:
    choice_y = _find_choice_y0(page, clip)
    if choice_y is not None and _has_significant_graphics_below_y(
        page,
        clip,
        float(choice_y),
        cluster_pad_pts=cluster_pad_pts,
        min_width_pts=min_width_pts,
        min_height_pts=min_height_pts,
        min_ratio=min_ratio,
        min_graphic_area_pts2=min_graphic_area_pts2,
    ):
        choice_y = None
    search = fitz.Rect(clip)
    if choice_y is not None:
        search.y1 = min(search.y1, choice_y - 2.0)
    if search.y1 <= search.y0 + 4.0:
        return None

    rects = _collect_graphic_rects(page, search, min_area_pts2=min_graphic_area_pts2)
    if not rects:
        return None

    clusters = _cluster_union(rects, pad_pts=cluster_pad_pts)
    # Filter by size first to avoid thin header lines
    filtered = [
        r
        for r in clusters
        if (r.x1 - r.x0) >= min_width_pts and (r.y1 - r.y0) >= min_height_pts
    ]
    if not filtered:
        return None

    # Choose by bbox area (pragmatic for diagrams/tables)
    bbox = max(filtered, key=lambda r: r.get_area())
    ratio = bbox.get_area() / search.get_area() if search.get_area() > 0 else 0.0
    if ratio < min_ratio:
        return None

    bbox = _expand_bbox_with_nearby_text(page, bbox, search, text_pad_pts=text_pad_pts)
    # Re-check size after expansion
    if (bbox.x1 - bbox.x0) < min_width_pts or (bbox.y1 - bbox.y0) < min_height_pts:
        return None

    return FigureCandidate(
        page_index=int(page.number),
        ratio=float(ratio),
        clip_rect=fitz.Rect(clip),
        search_rect=fitz.Rect(search),
        bbox=fitz.Rect(bbox),
        choice_y=choice_y,
    )


def extract_question_figures(
    pdf_path: Path,
    segment_id: str,
    out_dir: Path,
    *,
    scale: float,
    only: Optional[Set[int]] = None,
    limit: int = 0,
    min_ratio: float = 0.04,
    min_width_pts: float = 80.0,
    min_height_pts: float = 60.0,
    cluster_pad_pts: float = 40.0,
    text_pad_pts: float = 10.0,
    min_graphic_area_pts2: float = 10.0,
) -> Tuple[List[Path], List[Dict[str, object]]]:
    only = only or set()
    out_dir.mkdir(parents=True, exist_ok=True)

    doc = fitz.open(str(pdf_path))
    starts = _collect_start_positions(doc)
    if not starts:
        raise RuntimeError("No question starts detected. Check PDF text extraction.")

    q_nums = sorted(starts.keys())
    written: List[Path] = []
    manifest: List[Dict[str, object]] = []

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

        candidates: List[FigureCandidate] = []
        for pi in range(start_page, end_page + 1):
            page = doc[pi]
            W = float(page.rect.width)
            H = float(page.rect.height)

            if pi == start_page:
                y0 = max(0.0, float(start_y0) - TOP_PAD_PTS)
            else:
                y0 = 0.0

            if pi == end_page:
                y1 = float(end_y0) - BOTTOM_PAD_PTS
            else:
                y1 = H

            y1 = min(y1, H - BOTTOM_CUTOFF_PTS)
            if y1 <= y0 + 4.0:
                continue

            clip = fitz.Rect(0.0, y0, W, y1)
            cand = _best_figure_candidate_on_page(
                page,
                clip,
                min_ratio=min_ratio,
                min_width_pts=min_width_pts,
                min_height_pts=min_height_pts,
                cluster_pad_pts=cluster_pad_pts,
                text_pad_pts=text_pad_pts,
                min_graphic_area_pts2=min_graphic_area_pts2,
            )
            if cand:
                candidates.append(cand)

        if not candidates:
            continue

        # Render all page candidates (in page order) and stitch if needed.
        candidates.sort(key=lambda c: c.page_index)
        parts: List[Image.Image] = []
        for cand in candidates:
            page = doc[cand.page_index]
            parts.append(_render_clip(page, cand.bbox, scale=scale))

        stitched = _stitch_vertical(parts)

        q_id = f"{segment_id}-{q_num:03d}"
        file_base = q_id.replace("-", "_")
        out_path = out_dir / f"{file_base}.png"
        stitched.save(out_path, format="PNG", optimize=True)
        written.append(out_path)

        # Record the dominant candidate (largest bbox area)
        dom = max(candidates, key=lambda c: c.bbox.get_area())
        manifest.append(
            {
                "qId": q_id,
                "segmentId": segment_id,
                "qNum": q_num,
                "pdf": str(pdf_path),
                "pageIndex": dom.page_index,
                "ratio": round(dom.ratio, 6),
                "bbox": [round(dom.bbox.x0, 3), round(dom.bbox.y0, 3), round(dom.bbox.x1, 3), round(dom.bbox.y1, 3)],
                "choiceY": None if dom.choice_y is None else round(float(dom.choice_y), 3),
                "outFile": str(out_path),
            }
        )

    return written, manifest


def _write_manifest_csv(manifest_path: Path, rows: List[Dict[str, object]]) -> None:
    if not rows:
        # Still create a file for traceability.
        manifest_path.write_text(
            "qId,segmentId,qNum,pdf,pageIndex,ratio,bbox,choiceY,outFile\n",
            encoding="utf-8-sig",
        )
        return
    headers = ["qId", "segmentId", "qNum", "pdf", "pageIndex", "ratio", "bbox", "choiceY", "outFile"]
    # Use UTF-8 with BOM for compatibility with Excel/PowerShell on Windows.
    with manifest_path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=headers)
        w.writeheader()
        for r in rows:
            row = dict(r)
            # Store bbox as a compact string to keep CSV readable.
            bbox = row.get("bbox")
            if isinstance(bbox, list):
                row["bbox"] = "[" + ",".join(str(x) for x in bbox) + "]"
            w.writerow(row)


def _append_manifest_csv(manifest_path: Path, rows: List[Dict[str, object]]) -> None:
    if not rows:
        return
    if not manifest_path.exists():
        _write_manifest_csv(manifest_path, rows)
        return
    headers = ["qId", "segmentId", "qNum", "pdf", "pageIndex", "ratio", "bbox", "choiceY", "outFile"]
    # IMPORTANT: do not use utf-8-sig here, or a BOM may be appended mid-file.
    with manifest_path.open("a", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=headers)
        for r in rows:
            row = dict(r)
            bbox = row.get("bbox")
            if isinstance(bbox, list):
                row["bbox"] = "[" + ",".join(str(x) for x in bbox) + "]"
            w.writerow(row)


def main() -> None:
    ap = argparse.ArgumentParser(description="Extract per-question figure/table PNG images from PDF")
    ap.add_argument("--pdf", required=True, help="Input PDF file path")
    ap.add_argument("--segment-id", required=True, help="Segment ID (e.g., R7gakkaA)")
    ap.add_argument("--out-dir", default=str(_default_out_dir()), help="Output directory")
    ap.add_argument("--manifest", default="", help="Manifest CSV path (default: out-dir/figures_manifest.csv)")
    ap.add_argument("--append-manifest", action="store_true", help="Append to manifest CSV instead of overwriting")
    ap.add_argument("--scale", type=float, default=2.0, help="Render scale (2.0 ~= 144dpi)")
    ap.add_argument("--only", default="", help='Only these question numbers, e.g. "1-5,10,12"')
    ap.add_argument("--limit", type=int, default=0, help="Max number of images to write (0 = no limit)")
    ap.add_argument("--min-ratio", type=float, default=0.04, help="Min bbox area ratio vs search region")
    ap.add_argument("--min-width-pts", type=float, default=80.0, help="Min bbox width in PDF points")
    ap.add_argument("--min-height-pts", type=float, default=60.0, help="Min bbox height in PDF points")
    ap.add_argument("--cluster-pad-pts", type=float, default=40.0, help="Cluster merge padding in PDF points")
    ap.add_argument("--text-pad-pts", type=float, default=10.0, help="Pad for including nearby text labels")
    ap.add_argument("--min-graphic-area-pts2", type=float, default=10.0, help="Min graphic rect area to consider")
    args = ap.parse_args()

    pdf_path = Path(args.pdf)
    if not pdf_path.exists():
        raise SystemExit(f"PDF not found: {pdf_path}")

    out_dir = Path(args.out_dir)
    only = _parse_only(args.only)

    written, manifest = extract_question_figures(
        pdf_path=pdf_path,
        segment_id=str(args.segment_id),
        out_dir=out_dir,
        scale=float(args.scale),
        only=only,
        limit=int(args.limit),
        min_ratio=float(args.min_ratio),
        min_width_pts=float(args.min_width_pts),
        min_height_pts=float(args.min_height_pts),
        cluster_pad_pts=float(args.cluster_pad_pts),
        text_pad_pts=float(args.text_pad_pts),
        min_graphic_area_pts2=float(args.min_graphic_area_pts2),
    )

    manifest_path = Path(args.manifest) if str(args.manifest or "").strip() else (out_dir / "figures_manifest.csv")
    if args.append_manifest:
        _append_manifest_csv(manifest_path, manifest)
    else:
        _write_manifest_csv(manifest_path, manifest)

    print(f"Saved figures: {len(written)}")
    if written:
        print(f"First: {written[0]}")
    print(f"Out dir: {out_dir}")
    print(f"Manifest: {manifest_path}")


if __name__ == "__main__":
    main()
