"""Broad-QF zero-BER feasibility pilot using the real watermark/JPEG pipeline.

Uses a deliberately sparse d1 grid first; this is not an exhaustive optimum.
"""
from __future__ import annotations
import argparse
import csv
import json
from pathlib import Path
from dataclasses import asdict
import tempfile
import numpy as np
from PIL import Image
from experiments import adaptive_d1_grid as grid
from experiments.adaptive_d1_zero_ber_selection import select

QFS = (5, 10, 15, 20, 30, 50, 70, 90, 95)
D1_VALUES = tuple(sorted(set(range(1, 241, 4)) | {36, 90, 150, 240, 300, 400, 600, 720}))


def run(input_dir: Path, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    grid.QFS = QFS
    for source in sorted(input_dir.glob("*.png")):
        with Image.open(source) as im:
            rgb = np.asarray(im.convert("RGB"), dtype=np.uint8)
        folder = output_dir / source.stem
        folder.mkdir(exist_ok=True)
        rows = []
        per_qf_rows = []
        with tempfile.TemporaryDirectory() as tmp:
            for d1 in D1_VALUES:
                measurements = grid.evaluate_d1(rgb, d1, Path(tmp))
                result = grid.summarise(measurements)[0]
                rows.append(result)
                per_qf_rows.extend(asdict(item) for item in measurements)
                print(f"{source.name} d1={d1} worst_ber={result['worst_ber']:.5f}", flush=True)
                with (folder / "per_d1.csv").open("w", newline="", encoding="utf-8") as handle:
                    writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
                    writer.writeheader()
                    writer.writerows(rows)
        with (folder / "per_qf.csv").open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(per_qf_rows[0]))
            writer.writeheader()
            writer.writerows(per_qf_rows)
        baselines = {str(d): next((row for row in rows if row["d1"] == d), None) for d in (36, 90, 720)}
        report = {"image": source.name, "qfs": QFS, "d1_values": D1_VALUES,
                  "baseline_d1_36_90_720": baselines,
                  "note": "Sparse-grid feasibility pilot; absence of zero BER does not prove global infeasibility.",
                  **select(rows)}
        (folder / "zero_ber_result.json").write_text(json.dumps(report, indent=2) + "\n")
        print(json.dumps(report), flush=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    run(args.input_dir, args.output_dir)


if __name__ == "__main__":
    main()
