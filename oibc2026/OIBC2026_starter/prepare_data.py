"""Arrange the official OIBC 2026 data uploads in folders expected by baseline.py.

Usage from project folder:
    python prepare_data.py --source .
    python prepare_data.py --source "C:\\path\\to\\downloaded\\raw_files"
    python prepare_data.py --source . --dry-run

Keeps originals intact. '(1)' training vs unsuffixed test names match the
uploaded data checked against the supplied README and CSV time axes.
"""
from __future__ import annotations

import argparse
import shutil
from pathlib import Path

MAPPING = {
    "sites.csv": "sites.csv",
    "smp.csv": "smp.csv",  # evaluation: 8,760 rows and k column
    "smp(1).csv": "train/smp.csv",  # training: 38,688 rows
    "generation.parquet": "train/generation.parquet",
    "observed_wa.parquet": "train/observed_wa.parquet",
    "observed_wb.parquet": "train/observed_wb.parquet",
    "forecast_wa(1).parquet": "train/forecast_wa.parquet",
    "forecast_wb(1).parquet": "train/forecast_wb.parquet",
    "forecast_wa.parquet": "test/forecast_wa.parquet",
    "forecast_wb.parquet": "test/forecast_wb.parquet",
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare OIBC 2026 folder structure")
    parser.add_argument("--source", default=".", help="Directory holding downloaded raw files")
    parser.add_argument("--dest", default=str(Path(__file__).resolve().parent),
                        help="Project directory, defaults to the location of this script")
    parser.add_argument("--dry-run", action="store_true", help="Only show the planned copies")
    args = parser.parse_args()

    source = Path(args.source).expanduser().resolve()
    dest = Path(args.dest).expanduser().resolve()
    missing = [filename for filename in MAPPING if not (source / filename).is_file()]
    if missing:
        print("[ERROR] Files missing in", source)
        for item in missing:
            print(" -", item)
        raise SystemExit(1)

    for original, relative in MAPPING.items():
        src = source / original
        target = dest / relative
        if src == target:
            print(f"[OK] Already in place: {relative}")
            continue
        print(f"{'[PLAN]' if args.dry_run else '[COPY]'} {original} -> {relative} ({src.stat().st_size / 1024**2:.1f} MiB)")
        if not args.dry_run:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, target)
    if args.dry_run:
        print("[OK] All 10 required raw files found. No files copied.")
    else:
        print("[OK] Data folder structure ready. Next: python verify_env.py")


if __name__ == "__main__":
    main()
