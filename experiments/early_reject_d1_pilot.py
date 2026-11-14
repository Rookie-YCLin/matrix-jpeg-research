"""Real-JPEG pilot comparing unchanged V2 selector with safe early QF rejection.

Only candidate evaluation cost changes. No full-QF BER/mean is invented
for a rejected candidate. A selected feasible candidate has all nine QFs
measured with zero errors and a clean extraction with zero errors.
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
from experiments.adaptive_d1_zero_ber_pilot import QFS
from experiments.auto_zero_ber import select_step
from experiments.early_reject_policy import quality_screen, all_qfs_verified_zero
from experiments.svd_qim_psnr import rgb_psnr
from experiments.svd_qim_sweep import configured_instance, extract_with_qim


def save_csv(path: Path, rows: list[dict]) -> None:
    if rows:
        with path.open('w', newline='', encoding='utf-8') as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)


def evaluate_d1_early(
    rgb: np.ndarray, d1: int, temp: Path
) -> tuple[dict, list[grid.Evaluation]]:
    marked = temp / f'd1_{d1:03d}.png'
    records: list[grid.Evaluation] = []
    start_embed = perf_counter()
    wm = configured_instance(d1, grid.D2)
    wm.read_img(img=fixed.to_bgr(rgb))
    wm.read_wm([int(bit) for bit in fixed.PAYLOAD], mode='bit')
    wm.embed(filename=str(marked))
    embed_seconds = perf_counter() - start_embed
    try:
        marked_rgb = fixed.read_rgb(marked)
        png_mse, png_psnr = rgb_psnr(rgb, marked_rgb)
        clean_bits = extract_with_qim(marked_rgb, d1, grid.D2)
        clean_errors = grid.errors(fixed.PAYLOAD, clean_bits)

        def measure(qf: int) -> int:
            attacked = temp / f'd1_{d1:03d}_qf_{qf:02d}.jpg'
            started = perf_counter()
            try:
                with Image.open(marked) as image:
                    image.save(attacked, format='JPEG', quality=qf, **fixed.JPEG)
                bits = extract_with_qim(fixed.read_rgb(attacked), d1, grid.D2)
                elapsed = perf_counter() - started
                err = grid.errors(fixed.PAYLOAD, bits)
                records.append(grid.Evaluation(
                    d1=d1, qf=qf, errors=err, total_bits=fixed.WM_SIZE,
                    ber=err / fixed.WM_SIZE, extracted_bits=bits,
                    png_psnr_db=png_psnr, png_mse_rgb_8bit=png_mse,
                    clean_errors=clean_errors, embed_seconds=embed_seconds,
                    jpeg_extract_seconds=elapsed,
                ))
                return err
            finally:
                attacked.unlink(missing_ok=True)

        checked = quality_screen(QFS, clean_errors, measure)
        assert checked == tuple(row.qf for row in records)
        observed_errors = tuple(row.errors for row in records)
        verified = all_qfs_verified_zero(QFS, checked, clean_errors, observed_errors)
        # The observed worst BER is sufficient to reject a failing candidate;
        # unknown QFs have NO imputed BER values.
        observed_worst_ber = max(row.ber for row in records)
        assert verified == (clean_errors == 0 and observed_worst_ber == 0)
        row = {
            'd1': d1,
            'worst_ber': observed_worst_ber,
            'clean_errors': clean_errors,
            'png_psnr_db': png_psnr,
            'png_mse_rgb_8bit': png_mse,
            'jpeg_attacks': len(records),
            'tested_qfs': ','.join(str(q) for q in checked),
            # Actual measured per-QF bit errors; never impute skipped attacks.
            'qf_error_counts': ','.join(str(r.errors) for r in records),
            'skipped_qfs': ','.join(str(q) for q in QFS if q not in checked),
            'full_qf_verification': verified,
            'rejected_at_qf': (
                records[-1].qf if len(records) != len(QFS) else ''
            ),
            'observed_mean_ber': float(np.mean([r.ber for r in records])),
            'total_seconds': embed_seconds + sum(
                r.jpeg_extract_seconds for r in records),
        }
        return row, records
    finally:
        marked.unlink(missing_ok=True)


def run(input_dir: Path, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    images = sorted(input_dir.glob('*.png'))
    if not images:
        raise ValueError(f'No PNG images in {input_dir}')
    assert tuple(QFS) == (5, 10, 15, 20, 30, 50, 70, 90, 95)
    for source in images:
        with Image.open(source) as image:
            rgb = np.asarray(image.convert('RGB'), dtype=np.uint8)
        folder = output_dir / source.stem
        folder.mkdir(parents=True, exist_ok=True)
        per_d1: list[dict] = []
        per_qf: list[dict] = []
        started = perf_counter()
        with tempfile.TemporaryDirectory() as temp:
            def evaluate(d1: int) -> dict:
                row, records = evaluate_d1_early(rgb, d1, Path(temp))
                per_d1.append(row)
                per_qf.extend(asdict(x) for x in records)
                save_csv(folder / 'per_d1.csv', per_d1)
                save_csv(folder / 'per_qf.csv', per_qf)
                print(f'{source.stem} d1={d1} '
                      f'worst_observed_ber={row["worst_ber"]:.6f} '
                      f'jpeg_attacks={row["jpeg_attacks"]} '
                      f'PNG_PSNR={row["png_psnr_db"]:.4f}', flush=True)
                return row

            outcome = select_step(evaluate)
        wall_seconds = perf_counter() - started
        # Complete candidate rows only are allowed to be called verified feasible.
        for measurement, row in zip(outcome.measurements, per_d1):
            assert measurement.d1 == row['d1']
            assert measurement.feasible == row['full_qf_verification']
        trace = [{
            'order': i, 'd1': m.d1, 'reason': reason,
            'worst_observed_ber': m.worst_ber,
            'clean_errors': m.clean_errors,
            'psnr_db': m.psnr_db,
            'feasible_verified': m.feasible,
            'qfs_tested': per_d1[i-1]['tested_qfs'],
            'jpeg_attacks': per_d1[i-1]['jpeg_attacks'],
        } for i, (m, reason) in enumerate(
            zip(outcome.measurements, outcome.reasons), 1
        )]
        save_csv(folder / 'trace.csv', trace)
        manifest = {
            'image': source.name,
            'source_sha256': sha256(source.read_bytes()).hexdigest(),
            'shape_rgb': list(rgb.shape),
            'method': 'auto_zero_ber_v2_early_reject_qf5_first',
            'status': outcome.status,
            'qfs': list(QFS),
            'fixed_d2': grid.D2,
            'evaluations': outcome.evaluations,
            'jpeg_attacks': len(per_qf),
            'full_verification_jpeg_attacks_equivalent': outcome.evaluations * len(QFS),
            'saved_jpeg_attacks': outcome.evaluations * len(QFS) - len(per_qf),
            'wall_seconds': wall_seconds,
            'summed_measurement_seconds': sum(
                row['total_seconds'] for row in per_d1
            ),
            'best_d1': outcome.best_d1,
            'best_png_psnr_db': outcome.best_psnr_db,
            'candidate_d1_in_evaluation_order': [
                m.d1 for m in outcome.measurements
            ],
            'note': ('No BER values imputed for skipped QFs; '
                     'every selected feasible d1 is fully verified.'),
        }
        (folder / 'result.json').write_text(
            json.dumps(manifest, indent=2) + '\n', encoding='utf-8'
        )
        print(json.dumps(manifest), flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input-dir', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    run(args.input_dir, args.output_dir)


if __name__ == '__main__':
    main()
