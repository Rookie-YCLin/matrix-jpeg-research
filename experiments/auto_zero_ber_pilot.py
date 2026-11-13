"""Real-JPEG three-image pilot for automatic zero-BER-first d1 search.

The user never passes d1, step size, a candidate list or search bounds.
Every trial runs the existing pinned watermark/JPEG/extraction evaluator at
all nine predeclared QFs. CSVs contain *measured* values, not interpolations.
"""
from __future__ import annotations

import argparse
import csv
from dataclasses import asdict
from hashlib import sha256
import json
from pathlib import Path
import tempfile

import numpy as np
from PIL import Image

from experiments import adaptive_d1_grid as grid
from experiments.adaptive_d1_zero_ber_pilot import QFS
from experiments.auto_zero_ber import select_step


def _write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        return
    with path.open('w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def run(input_dir: Path, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    grid.QFS = QFS
    images = sorted(input_dir.glob('*.png'))
    if not images:
        raise ValueError(f'No PNG input images in {input_dir}')

    for source in images:
        with Image.open(source) as image:
            rgb = np.asarray(image.convert('RGB'), dtype=np.uint8)
        folder = output_dir / source.stem
        folder.mkdir(parents=True, exist_ok=True)
        per_d1: list[dict] = []
        per_qf: list[dict] = []
        with tempfile.TemporaryDirectory() as temp:
            def evaluate(d1: int) -> dict:
                records = grid.evaluate_d1(rgb, d1, Path(temp))
                row = grid.summarise(records)[0]
                assert row['d1'] == d1
                per_d1.append(row)
                per_qf.extend(asdict(record) for record in records)
                # Persist each completed evaluation, including on an eventual
                # workflow timeout or unexpected exception.
                _write_csv(folder / 'per_d1.csv', per_d1)
                _write_csv(folder / 'per_qf.csv', per_qf)
                print(f'{source.stem} d1={d1} '
                      f'worst_ber={row["worst_ber"]:.6f} '
                      f'PSNR={row["png_psnr_db"]:.4f}', flush=True)
                return row

            outcome = select_step(evaluate)

        trace = [{
            'order': index,
            'd1': measurement.d1,
            'reason': reason,
            'worst_ber': measurement.worst_ber,
            'clean_errors': measurement.clean_errors,
            'psnr_db': measurement.psnr_db,
            'feasible': measurement.feasible,
        } for index, (measurement, reason) in
            enumerate(zip(outcome.measurements, outcome.reasons), 1)]
        _write_csv(folder / 'trace.csv', trace)
        manifest = {
            'image': source.name,
            'source_sha256': sha256(source.read_bytes()).hexdigest(),
            'shape_rgb': list(rgb.shape),
            'method': 'auto_zero_ber_v1',
            'status': outcome.status,
            'qfs': list(QFS),
            'fixed_d2': grid.D2,
            'evaluations': outcome.evaluations,
            'jpeg_attacks': len(per_qf),
            'best_d1': outcome.best_d1,
            'best_png_psnr_db': outcome.best_psnr_db,
            'candidate_d1_in_evaluation_order': [m.d1 for m in outcome.measurements],
            'note': 'No global optimality, no claim for untested JPEG QFs.',
        }
        (folder / 'result.json').write_text(
            json.dumps(manifest, indent=2) + '\n', encoding='utf-8'
        )
        print(json.dumps(manifest), flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input-dir', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    arguments = parser.parse_args()
    run(arguments.input_dir, arguments.output_dir)


if __name__ == '__main__':
    main()
