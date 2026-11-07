"""Run the approved first-stage experiment from a local grayscale PNG."""
import argparse
import csv
from hashlib import sha256
from importlib.metadata import version
import json
from pathlib import Path
import platform
import sys
import traceback

import numpy as np
from PIL import features

import charts
import imaging
import svd

RANKS = (1, 5, 10, 20, 50, 100)


def write_csv(path, rows):
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def run(input_path, output):
    payload = input_path.read_bytes()
    pixels = imaging.read_gray_png(payload)
    if min(pixels.shape) < max(RANKS):
        raise ValueError("Both image dimensions must be at least 100")
    output.mkdir(parents=True, exist_ok=False)
    try:
        original = pixels.astype(np.float64)
        jpeg_path = output / "jpeg_q80.jpg"
        decoded = imaging.jpeg_round_trip(pixels, jpeg_path)
        imaging.save_display(decoded, output / "jpeg_decoded.png")
        error_rows, spectrum_rows = [], []
        validation = {}
        for name, matrix in (("original", original), ("jpeg_q80", decoded)):
            factors = svd.decompose(matrix)
            rows = svd.validate(matrix, factors, RANKS)
            error_rows.extend({"image": name, **row} for row in rows)
            validation[name] = {
                "checked_ranks": [row["k"] for row in rows],
                "max_relative_identity_gap": max(
                    abs(row["relative_squared"] - row["relative_tail_squared"]) for row in rows
                ),
                "full_reconstruction_relative_squared": rows[-1]["relative_squared"],
            }
            singular_values = factors[1]
            squared = singular_values**2
            cumulative = np.cumsum(squared) / (float(np.sum(squared)) or 1.0)
            spectrum_rows.extend({
                "image": name, "i": i, "sigma": sigma, "cumulative_energy": fraction,
            } for i, (sigma, fraction) in enumerate(zip(singular_values, cumulative), start=1))
            if name == "original":
                for k in RANKS:
                    imaging.save_display(svd.reconstruct(factors, k), output / f"rank_{k:03}.png")

        mse, psnr = imaging.quality_metrics(original, decoded)
        write_csv(output / "rank_errors.csv", error_rows)
        write_csv(output / "spectrum.csv", spectrum_rows)
        write_csv(output / "jpeg_metrics.csv", [{
            "quality_factor": imaging.JPEG_SETTINGS["quality"],
            "jpeg_bytes": jpeg_path.stat().st_size, "mse": mse, "psnr_db": psnr,
        }])
        charts.render(output, pixels, RANKS)
        manifest = {
            "status": "passed",
            "input": {"path": str(input_path), "sha256": sha256(payload).hexdigest(),
                      "shape": list(pixels.shape), "mode": "L"},
            "python": platform.python_version(),
            "platform": platform.platform(),
            "packages": {name: version(name) for name in ("numpy", "Pillow", "matplotlib")},
            "jpeg_library": features.version_codec("jpg"),
            "libjpeg_turbo": features.version_feature("libjpeg_turbo"),
            "jpeg_settings": imaging.JPEG_SETTINGS,
            "validation": {"rtol": svd.RTOL, "atol": svd.ATOL, **validation},
            "artifacts": sorted(path.name for path in output.iterdir()),
        }
        (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n",
                                               encoding="utf-8")
    except Exception:
        (output / "failure.txt").write_text(traceback.format_exc(), encoding="utf-8")
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    try:
        run(args.input, args.output_dir)
    except (ValueError, OSError, AssertionError, np.linalg.LinAlgError) as error:
        print(f"Experiment failed: {error}", file=sys.stderr)
        return 1
    print(f"Experiment passed: {args.output_dir / 'manifest.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
