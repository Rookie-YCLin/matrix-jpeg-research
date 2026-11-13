"""Real-JPEG, nine-QF, per-image DIRECT-inspired trial (no user d1 tuning).

The data and target QFs match auto_zero_ber_pilot.py; one 36-unique-d1
budget per image. This runner NEVER reads grid or V2 output to choose d1.
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
from experiments.direct_d1 import select_direct_step


def save_csv(path: Path, rows: list[dict]) -> None:
    if rows:
        with path.open('w', encoding='utf-8', newline='') as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)


def run(input_dir: Path, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    grid.QFS = QFS
    images = sorted(input_dir.glob('*.png'))
    if not images:
        raise ValueError(f'No PNG images at {input_dir}')
    for source in images:
        with Image.open(source) as image:
            rgb = np.asarray(image.convert('RGB'), dtype=np.uint8)
        folder = output_dir / source.stem
        folder.mkdir(parents=True, exist_ok=True)
        per_d1: list[dict] = []
        per_qf: list[dict] = []
        start = perf_counter()
        with tempfile.TemporaryDirectory() as temp:
            def evaluate(d1: int) -> dict:
                records = grid.evaluate_d1(rgb, d1, Path(temp))
                row = grid.summarise(records)[0]
                assert row['d1'] == d1 and len(records) == len(QFS)
                per_d1.append(row)
                per_qf.extend(asdict(record) for record in records)
                save_csv(folder / 'per_d1.csv', per_d1)
                save_csv(folder / 'per_qf.csv', per_qf)
                print(f'{source.stem} d1={d1} '
                      f'worst_ber={row["worst_ber"]:.6f} '
                      f'psnr={row["png_psnr_db"]:.4f}', flush=True)
                return row

            result = select_direct_step(evaluate)
        wall_seconds = perf_counter() - start
        trace = [{
            'order': index, 'd1': item.d1, 'reason': reason,
            'worst_ber': item.worst_ber,
            'clean_errors': item.clean_errors,
            'psnr_db': item.psnr_db,
            'feasible': item.feasible,
        } for index, (item, reason) in
            enumerate(zip(result.measurements, result.reasons), 1)]
        save_csv(folder / 'trace.csv', trace)
        manifest = {
            'image': source.name,
            'source_sha256': sha256(source.read_bytes()).hexdigest(),
            'shape_rgb': list(rgb.shape),
            'method': 'discrete_directgo_inspired_v1',
            'source_reference': 'blockchain-group/DIRECTGO Algorithms/dX_DTC_GL.m',
            'status': result.status,
            'qfs': list(QFS),
            'fixed_d2': grid.D2,
            'evaluations': result.evaluations,
            'jpeg_attacks': len(per_qf),
            'wall_seconds': wall_seconds,
            'summed_measurement_seconds': sum(float(row['total_seconds']) for row in per_d1),
            'best_d1': result.best_d1,
            'best_png_psnr_db': result.best_psnr_db,
            'candidate_d1_in_evaluation_order': [m.d1 for m in result.measurements],
            'note': 'Measured QFs only. No global optimality or untested-QF claims.',
        }
        (folder / 'result.json').write_text(
            json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
        print(json.dumps(manifest), flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input-dir', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    run(args.input_dir, args.output_dir)


if __name__ == '__main__':
    main()
