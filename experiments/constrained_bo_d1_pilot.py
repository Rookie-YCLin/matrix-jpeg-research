"""Real-JPEG BO pilot using the same evaluator as V2 early-rejection search.

Writes actual measured JPEG QFs only. Optional --compare-v2 performs a
paired budget-36 V2 run using the same source image and embedding settings.
"""
from __future__ import annotations

import argparse
import csv
from dataclasses import asdict
from hashlib import sha256
import json
from pathlib import Path
import tempfile
from time import perf_counter

import numpy as np
from PIL import Image

from experiments import adaptive_d1_grid as grid
from experiments.adaptive_d1_zero_ber_pilot import QFS
from experiments.auto_zero_ber import select_step as v2_select_step
from experiments.constrained_bo_d1 import select_step as bo_select_step
from experiments.early_reject_d1_pilot import evaluate_d1_early


def _csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        return
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _run_method(rgb: np.ndarray, source: Path, folder: Path, method: str) -> dict:
    folder.mkdir(parents=True, exist_ok=True)
    per_d1: list[dict] = []
    per_qf: list[dict] = []
    started = perf_counter()
    with tempfile.TemporaryDirectory() as tmp:
        def evaluate(d1: int) -> dict:
            row, records = evaluate_d1_early(rgb, d1, Path(tmp))
            per_d1.append(row)
            per_qf.extend(asdict(record) for record in records)
            _csv(folder / "per_d1.csv", per_d1)
            _csv(folder / "per_qf.csv", per_qf)
            print(f"{source.stem} {method} d1={d1} "
                  f"QF_checks={row['jpeg_attacks']} "
                  f"full_feasible={row['full_qf_verification']} "
                  f"PSNR={row['png_psnr_db']:.4f}", flush=True)
            return row

        result = bo_select_step(evaluate) if method == "bo" else v2_select_step(evaluate)
    wall = perf_counter() - started
    trace = []
    for i, (measurement, reason) in enumerate(
        zip(result.observations if method == "bo" else result.measurements,
            result.reasons), 1
    ):
        row = per_d1[i - 1]
        assert measurement.d1 == row["d1"]
        verified = row["full_qf_verification"]
        if method == "bo":
            assert measurement.verified_feasible == verified
        else:
            assert measurement.feasible == verified
        trace.append({
            "order": i, "d1": measurement.d1, "reason": reason,
            "psnr_db": row["png_psnr_db"],
            "verified_feasible": verified,
            "tested_qfs": row["tested_qfs"],
            "jpeg_attacks": row["jpeg_attacks"],
        })
    _csv(folder / "trace.csv", trace)
    outcome = {
        "image": source.name,
        "source_sha256": sha256(source.read_bytes()).hexdigest(),
        "shape_rgb": list(rgb.shape),
        "method": "integer_constrained_bo_gp_eic" if method == "bo" else "v2_early_rejection",
        "status": result.status,
        "fixed_d2": grid.D2,
        "qfs": list(QFS),
        "evaluations": result.evaluations,
        "jpeg_attacks": len(per_qf),
        "wall_seconds": wall,
        "best_d1": result.best_d1,
        "best_png_psnr_db": result.best_psnr_db,
        "verified_feasible_candidates": sum(bool(r["full_qf_verification"]) for r in per_d1),
        "candidate_d1_in_evaluation_order": [r["d1"] for r in per_d1],
        "note": "No synthetic evidence or BER imputation; no global optimum claim.",
    }
    (folder / "result.json").write_text(
        json.dumps(outcome, indent=2) + "\n", encoding="utf-8"
    )
    return outcome


def run(input_dir: Path, output_dir: Path, compare_v2: bool = False) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    sources = sorted(input_dir.glob("*.png"))
    if not sources:
        raise ValueError(f"No PNG input images in {input_dir}")
    if tuple(QFS) != (5, 10, 15, 20, 30, 50, 70, 90, 95):
        raise AssertionError("Changed nine-QF research protocol")
    for source in sources:
        with Image.open(source) as image:
            rgb = np.asarray(image.convert("RGB"), dtype=np.uint8)
        folder = output_dir / source.stem
        bo = _run_method(rgb, source, folder / "bo", "bo")
        if compare_v2:
            v2 = _run_method(rgb, source, folder / "v2", "v2")
            comparison = {
                "image": source.name, "bo": bo, "v2": v2,
                "psnr_difference_db": (
                    bo["best_png_psnr_db"] - v2["best_png_psnr_db"]
                    if bo["best_png_psnr_db"] is not None
                    and v2["best_png_psnr_db"] is not None else None
                ),
                "jpeg_attack_difference": bo["jpeg_attacks"] - v2["jpeg_attacks"],
                "wall_seconds_difference": bo["wall_seconds"] - v2["wall_seconds"],
                "note": "Equal number of candidate evaluations; runtime includes surrogate fitting.",
            }
            (folder / "comparison.json").write_text(
                json.dumps(comparison, indent=2) + "\n", encoding="utf-8"
            )
            print(json.dumps(comparison), flush=True)
        else:
            print(json.dumps(bo), flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--compare-v2", action="store_true")
    args = parser.parse_args()
    run(args.input_dir, args.output_dir, compare_v2=args.compare_v2)


if __name__ == "__main__":
    main()
