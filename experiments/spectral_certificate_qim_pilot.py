"""Execute a mathematically certified finite-domain SVD-QIM optimization.

Scores all 720 d1 analytically from the ORIGINAL upstream DCT-SVD blocks,
then calls the unchanged real Pillow JPEG / blind extractor on candidates
in ascending *exact transform-domain* distortion. First complete zero-BER
candidate is globally optimal for that transform-domain metric.

For comparison, optional legacy V2 uses the same source, 32 bits, QF set,
PNG PSNR and early rejection. We do NOT assert RGB-PSNR global optimality.
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
from experiments import ori_qf_scan as fixed
from experiments.constrained_bo_d1_pilot import _run_method as run_legacy_method
from experiments.early_reject_d1_pilot import evaluate_d1_early
from experiments.spectral_certificate_qim import (
    DOMAIN, QFS, upstream_spectral_profile, select_certified,
)
from experiments.exact_rgb_objective import exact_png_rgb_mse_profile
from experiments.svd_qim_psnr import rgb_psnr
from experiments.svd_qim_sweep import configured_instance, extract_with_qim


def _write_csv(path: Path, rows: list[dict]) -> None:
    if rows:
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)


def run_one(source: Path, folder: Path, *, max_evaluations: int = len(DOMAIN),
            compare_v2: bool = False, objective: str = "rgb_mse") -> dict:
    folder.mkdir(parents=True, exist_ok=True)
    with Image.open(source) as image:
        rgb = np.asarray(image.convert("RGB"), dtype=np.uint8)
    if tuple(QFS) != (5, 10, 15, 20, 30, 50, 70, 90, 95) or grid.D2 != 20:
        raise AssertionError("Changed fixed zero-BER research protocol")

    begin = perf_counter()
    if objective not in ("spectral", "rgb_mse"):
        raise ValueError("objective must be spectral or rgb_mse")
    energies = (upstream_spectral_profile(rgb) if objective == "spectral"
                else exact_png_rgb_mse_profile(rgb))
    score_seconds = perf_counter() - begin
    ranked = sorted(DOMAIN, key=lambda d: (energies[d], d))
    _write_csv(folder / "all_720_ranked_objectives.csv", [
        {"rank": rank, "d1": d, "objective_value": energies[d]}
        for rank, d in enumerate(ranked, 1)
    ])
    real_rows: list[dict] = []
    qf_rows: list[dict] = []

    with tempfile.TemporaryDirectory() as temp:
        def evaluate(d1: int) -> dict:
            row, measured_qfs = evaluate_d1_early(rgb, d1, Path(temp))
            real_rows.append({**row, "objective_value": energies[d1]})
            qf_rows.extend(asdict(record) for record in measured_qfs)
            # Atomic-ish incremental archival so real measurements survive even
            # if an out-of-budget run is interrupted.
            _write_csv(folder / "per_d1.csv", real_rows)
            _write_csv(folder / "per_qf.csv", qf_rows)
            print(
                f"{source.stem} rank={len(real_rows)} d1={d1} "
                f"qf_checks={row['jpeg_attacks']} "
                f"all_zero={row['full_qf_verification']}",
                flush=True,
            )
            return row

        outcome = select_certified(
            energies, evaluate, max_evaluations=max_evaluations,
            objective=objective,
        )
    total_seconds = perf_counter() - begin
    if len(real_rows) != outcome.evaluations:
        raise AssertionError("Observed evaluations do not match certificate")

    manifest = {
        "source": source.name,
        "sha256_source_png": sha256(source.read_bytes()).hexdigest(),
        "shape_rgb": list(rgb.shape),
        "algorithm": "qim_exact_finite_domain_feasibility_certificate",
        "objective": objective,
        "status": outcome.status,
        "certified": outcome.certified,
        "domain_scored": list([DOMAIN[0], DOMAIN[-1]]),
        "all_integer_steps_scored": len(energies),
        "score_name": (
            "actual_uint8_rgb_png_mse" if objective == "rgb_mse" else
            "sum_per_block_delta_sigma0_squared_plus_delta_sigma1_squared"
        ),
        "score_interpretation": (
            "Exact uint8 RGB PNG MSE including all upstream encoding effects"
            if objective == "rgb_mse" else
            "Exact SVD/DCT-domain Frobenius squared perturbation; "
            "not equal to uint8 RGB MSE"
        ),
        "optimality_scope": (
            ("Global maximum of actual uint8 PNG RGB PSNR" if objective == "rgb_mse"
             else "Global minimum of exact transform-domain Frobenius energy")
            + " among all integer d1=1..720 with actual clean and nine-QF "
              "zero bit error certificates"
        ) if outcome.status == f"certified_{objective}_global_optimum"
        else "No global feasible optimality claim when search incomplete",
        "fixed_d2": grid.D2,
        "qfs": list(QFS),
        "best_d1": outcome.best_d1,
        "best_objective_value": outcome.best_transform_energy,
        "best_actual_png_psnr_db": outcome.best_png_psnr_db,
        "evaluated_d1_count": outcome.evaluations,
        "actual_jpeg_attacks": len(qf_rows),
        "scoring_seconds": score_seconds,
        "total_wall_seconds": total_seconds,
        "sequence": list(outcome.attempted_steps),
        "clean_and_full_qf_required": True,
        "note": ("Every selected step has nine REAL measured JPEG zero-error "
                 "checks. Neither BER monotonicity nor QF independence is assumed. "
                 "Spectral scores prove only spectral optimum; RGB MSE scores prove "
                 "global PNG PSNR optimum for the fixed 720-element domain."),
    }
    if outcome.status == f"certified_{objective}_global_optimum":
        # Persist the real marked image selected by the exact upstream embedder.
        destination = folder / "selected_marked.png"
        wm = configured_instance(outcome.best_d1, grid.D2)
        wm.read_img(img=fixed.to_bgr(rgb))
        wm.read_wm([int(x) for x in fixed.PAYLOAD], mode="bit")
        wm.embed(filename=str(destination))
        restored = fixed.read_rgb(destination)
        _, measured_psnr = rgb_psnr(rgb, restored)
        if abs(measured_psnr - outcome.best_png_psnr_db) > 1e-8:
            raise AssertionError("Re-embedded winner differs from measured PNG")
        if grid.errors(
            fixed.PAYLOAD, extract_with_qim(restored, outcome.best_d1, grid.D2)
        ) != 0:
            raise AssertionError("Exported marked PNG clean extraction failed")
        manifest["marked_sha256"] = sha256(destination.read_bytes()).hexdigest()

    (folder / "result.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    if compare_v2:
        legacy = run_legacy_method(rgb, source, folder / "legacy_v2", "v2")
        comparison = {
            "source": source.name,
            "certificate": manifest,
            "legacy_v2": legacy,
            "actual_png_psnr_difference_db": (
                manifest["best_actual_png_psnr_db"] - legacy["best_png_psnr_db"]
                if manifest["best_actual_png_psnr_db"] is not None and
                   legacy["best_png_psnr_db"] is not None else None
            ),
            "actual_jpeg_check_difference": (
                manifest["actual_jpeg_attacks"] - legacy["jpeg_attacks"]
            ),
            "wall_seconds_difference": (
                manifest["total_wall_seconds"] - legacy["wall_seconds"]
            ),
            "fairness_note": (
                "No equal-36-budget claim. This method ranks all 720 "
                "candidates and may use more JPEG calls. Legacy V2 uses "
                "36 candidate evaluations. Compare PSNR and total cost; "
                "spectral and RGB objectives are distinctly named."
            ),
        }
        (folder / "comparison.json").write_text(
            json.dumps(comparison, indent=2) + "\n", encoding="utf-8"
        )
        print(
            json.dumps({
                "image": source.name,
                "spectral_certified": manifest["certified"],
                "selected_d1": manifest["best_d1"],
                "selected_rgb_psnr_db": manifest["best_actual_png_psnr_db"],
                "legacy_rgb_psnr_db": legacy["best_png_psnr_db"],
                "difference_db": comparison["actual_png_psnr_difference_db"],
                "spectral_candidate_count": manifest["evaluated_d1_count"],
                "spectral_jpeg_checks": manifest["actual_jpeg_attacks"],
                "legacy_jpeg_checks": legacy["jpeg_attacks"],
            }), flush=True,
        )
    else:
        print(json.dumps(manifest), flush=True)
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--max-evaluations", type=int, default=len(DOMAIN))
    parser.add_argument("--compare-v2", action="store_true")
    parser.add_argument("--objective", choices=("rgb_mse", "spectral"),
                        default="rgb_mse")
    args = parser.parse_args()
    files = sorted(args.input_dir.glob("*.png"))
    if not files:
        raise ValueError("No source PNGs")
    for file in files:
        run_one(
            file, args.output_dir / file.stem,
            max_evaluations=args.max_evaluations,
            compare_v2=args.compare_v2,
            objective=args.objective,
        )


if __name__ == "__main__":
    main()
