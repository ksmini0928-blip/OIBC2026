"""Quick environment/data integrity checks. Does not train the model."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
EXPECTED = {
    "sites.csv": None,
    "smp.csv": None,
    "train/smp.csv": None,
    "train/generation.parquet": 4_392_566,
    "train/forecast_wa.parquet": 4_710_356,
    "train/forecast_wb.parquet": 5_621_996,
    "train/observed_wa.parquet": 2_359_974,
    "train/observed_wb.parquet": 2_824_223,
    "test/forecast_wa.parquet": 1_068_456,
    "test/forecast_wb.parquet": 1_278_960,
}


def main() -> None:
    print("Python:", sys.version.split()[0])
    if sys.version_info < (3, 10):
        print("[ERROR] Python 3.10+ required for baseline.py annotations")
        raise SystemExit(1)

    try:
        import numpy
        import pandas as pd
        import pyarrow.parquet as pq
        import lightgbm
        import sklearn
    except ImportError as exc:
        print("[ERROR] Missing Python module:", exc)
        print("Install it: python -m pip install -r requirements.txt")
        raise SystemExit(1) from exc

    for name, obj in [("numpy", numpy), ("pandas", pd), ("lightgbm", lightgbm), ("sklearn", sklearn)]:
        print(f"[OK] {name}: {obj.__version__}")

    missing = [item for item in EXPECTED if not (ROOT / item).is_file()]
    if missing:
        print("[ERROR] Missing data files:")
        for item in missing:
            print(" -", item)
        print("Run: python prepare_data.py --source <raw data directory>")
        raise SystemExit(1)

    sites = pd.read_csv(ROOT / "sites.csv")
    score = pd.read_csv(ROOT / "smp.csv")
    train_smp = pd.read_csv(ROOT / "train/smp.csv")
    ok = True
    print(f"[CHECK] sites.csv: {len(sites)} sites, sum capacity {sites.capacity_kw.sum():,.2f} kW")
    ok &= len(sites) == 253 and sites.site_id.nunique() == 253
    ok &= 42654 < sites.capacity_kw.sum() < 42657
    print(f"[CHECK] smp.csv: {len(score):,} rows, cols {list(score.columns)}")
    print(f"[CHECK] train/smp.csv: {len(train_smp):,} rows")
    ok &= len(score) == 8760 and all(x in score.columns for x in ("ts", "smp", "k"))
    ok &= len(train_smp) == 38688 and "k" not in train_smp.columns

    cap = sites.groupby("current_group").capacity_kw.sum()
    print("[CHECK] reference group capacities:", ", ".join(f"{g}={v:,.2f} kW" for g, v in cap.items()))
    ok &= len(cap) == 2 and all(cap >= 20_000)
    for relative, expected_rows in EXPECTED.items():
        if expected_rows is None:
            continue
        pf = pq.ParquetFile(ROOT / relative)
        rows = pf.metadata.num_rows
        matched = rows == expected_rows
        print(f"[{'OK' if matched else 'ERROR'}] {relative}: {rows:,} rows (expected {expected_rows:,})")
        ok &= matched

    if not ok:
        print("[ERROR] Some checks failed. Verify names and training/test mapping.")
        raise SystemExit(1)
    print("\n[SUCCESS] Ready to run the official baseline.")
    print("Command: python baseline.py --sites-out site_forecast.parquet")
    print("Note: scoring.py was not among the supplied uploads. It is not needed for baseline.py to generate CSVs.")


if __name__ == "__main__":
    main()
