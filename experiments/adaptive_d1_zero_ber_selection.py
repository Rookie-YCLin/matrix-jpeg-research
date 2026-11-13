"""Zero-BER-first selection from measured real-JPEG per_d1.csv files.

This is an analysis baseline, not a claim of zero BER for unseen JPEG QFs.
Feasibility requires clean_errors==0 and worst_ber==0 across measured QFs.
If no feasible point exists, report infeasible; never silently relabel a
positive-BER point as success.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


def select(rows: list[dict], *, psnr_floor: float | None = None) -> dict:
    if not rows:
        raise ValueError("No measured candidates")
    candidates = []
    for row in rows:
        d = int(row["d1"])
        worst = float(row["worst_ber"])
        psnr = float(row["png_psnr_db"])
        clean = int(row["clean_errors"])
        if not (0 <= worst <= 1):
            raise ValueError(f"Invalid BER at d1={d}")
        candidates.append((d, worst, psnr, clean))
    if len({r[0] for r in candidates}) != len(candidates):
        raise ValueError("Duplicate d1 candidates")
    feasible = [r for r in candidates if r[1] == 0 and r[3] == 0
                and (psnr_floor is None or r[2] >= psnr_floor)]
    # Maximize image quality; smaller d1 breaks equal-PSNR ties.
    best = min(feasible, key=lambda r: (-r[2], r[0])) if feasible else None
    # Diagnostic only: no feasibility claims for this candidate.
    near = min(candidates, key=lambda r: (r[1], r[3], -r[2], r[0]))
    return {
        "status": "feasible" if best else "infeasible_in_measured_domain",
        "evaluations": len(candidates),
        "zero_ber_candidates": len(feasible),
        "best_zero_ber_d1": best[0] if best else None,
        "best_zero_ber_psnr_db": best[2] if best else None,
        "diagnostic_lowest_ber_d1": near[0],
        "diagnostic_lowest_worst_ber": near[1],
        "psnr_floor_db": psnr_floor,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv_files", nargs="+", type=Path)
    parser.add_argument("--psnr-floor", type=float)
    args = parser.parse_args()
    for path in args.csv_files:
        with path.open(newline="", encoding="utf-8") as handle:
            result = select(list(csv.DictReader(handle)), psnr_floor=args.psnr_floor)
        print(json.dumps({"file": str(path), **result}, ensure_ascii=False))


if __name__ == "__main__":
    main()
