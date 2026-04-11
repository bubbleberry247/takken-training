"""
Populate QuestionBank CSV imageUrl column for doboku-14w-training.

Assumptions:
  - qId format:   R7gakkaA-001
  - image file:  R7gakkaA_001.png (qId with '-' replaced by '_')
  - images live under:
      PDF-RakuRaku-Seisan/docs/assets/doboku-14w/images

By default this script updates the CSV in-place and writes a timestamped backup
next to it.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
from pathlib import Path
from typing import Dict, List, Tuple


DEFAULT_BASE_URL = (
    "https://raw.githubusercontent.com/bubbleberry247/PDF-RakuRaku-Seisan/"
    "master/docs/assets/doboku-14w/images/"
)


def _default_images_dir() -> Path:
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


def _ensure_trailing_slash(url: str) -> str:
    url = (url or "").strip()
    if not url:
        return url
    return url if url.endswith("/") else url + "/"


def _backup_path(csv_path: Path) -> Path:
    ts = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    return csv_path.with_name(f"{csv_path.stem}__bak_{ts}{csv_path.suffix}")


def _image_filename_for_qid(qid: str) -> str:
    # qId format: R7gakkaA-001 → filename: R7gakkaA-001.png (keep hyphen)
    return qid + ".png"


def populate_image_urls(
    csv_path: Path,
    images_dir: Path,
    base_url: str,
    *,
    only_empty: bool,
    dry_run: bool,
) -> Dict[str, object]:
    base_url = _ensure_trailing_slash(base_url)
    if not base_url:
        raise ValueError("--base-url is required")

    if not csv_path.exists():
        raise FileNotFoundError(f"CSV not found: {csv_path}")
    if not images_dir.exists():
        raise FileNotFoundError(f"Images dir not found: {images_dir}")

    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            raise ValueError("CSV has no header row")
        fieldnames = list(reader.fieldnames)
        if "qId" not in fieldnames or "imageUrl" not in fieldnames:
            raise ValueError("CSV must contain 'qId' and 'imageUrl' columns")
        rows: List[Dict[str, str]] = list(reader)

    updated = 0
    missing_files: List[Tuple[str, str]] = []

    for row in rows:
        qid = (row.get("qId") or "").strip()
        if not qid:
            continue
        if only_empty and (row.get("imageUrl") or "").strip():
            continue

        fn = _image_filename_for_qid(qid)
        img_path = images_dir / fn
        if not img_path.exists():
            missing_files.append((qid, fn))
            continue

        url = base_url + fn
        prev = (row.get("imageUrl") or "").strip()
        if prev == url:
            continue
        row["imageUrl"] = url
        updated += 1

    if dry_run:
        return {
            "ok": True,
            "dryRun": True,
            "csv": str(csv_path),
            "imagesDir": str(images_dir),
            "baseUrl": base_url,
            "rows": len(rows),
            "updated": updated,
            "missingFiles": len(missing_files),
            "missingSamples": missing_files[:5],
        }

    backup = _backup_path(csv_path)
    backup.write_bytes(csv_path.read_bytes())

    with csv_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return {
        "ok": True,
        "dryRun": False,
        "csv": str(csv_path),
        "backup": str(backup),
        "imagesDir": str(images_dir),
        "baseUrl": base_url,
        "rows": len(rows),
        "updated": updated,
        "missingFiles": len(missing_files),
        "missingSamples": missing_files[:5],
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="Populate QuestionBank CSV imageUrl from local images")
    ap.add_argument(
        "--csv",
        default=str(Path(__file__).with_name("questionbank_complete.csv")),
        help="Path to QuestionBank CSV (default: tools/questionbank_complete.csv)",
    )
    ap.add_argument(
        "--images-dir",
        default=str(_default_images_dir()),
        help="Directory containing PNG images",
    )
    ap.add_argument(
        "--base-url",
        default=DEFAULT_BASE_URL,
        help="Base URL to publish images (must be publicly accessible)",
    )
    ap.add_argument(
        "--only-empty",
        action="store_true",
        help="Only populate rows whose imageUrl is empty",
    )
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="Do not write changes; print stats only",
    )
    args = ap.parse_args()

    res = populate_image_urls(
        csv_path=Path(args.csv),
        images_dir=Path(args.images_dir),
        base_url=str(args.base_url),
        only_empty=bool(args.only_empty),
        dry_run=bool(args.dry_run),
    )

    # Keep output stable and easy to grep.
    print(res)


if __name__ == "__main__":
    main()

