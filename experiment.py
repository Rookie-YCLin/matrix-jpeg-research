"""Compare original and JPEG-decoded grayscale matrices."""
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


def run(input_path, output, qualities=None):
    compare = qualities is not None
    qualities = tuple(qualities) if compare else (imaging.JPEG_SETTINGS["quality"],)
    if not qualities or len(set(qualities)) != len(qualities) or any(
        not 1 <= quality <= 95 for quality in qualities
    ):
        raise ValueError("Choose distinct JPEG quality factors from 1 through 95")
    payload = input_path.read_bytes()
    pixels = imaging.read_gray_png(payload)
    if min(pixels.shape) < max(RANKS):
        raise ValueError("Both image dimensions must be at least 100")
    output.mkdir(parents=True, exist_ok=False)
    try:
        original = pixels.astype(np.float64)
        original_factors = svd.decompose(original)
        original_sigma = original_factors[1]
        labels = {"original": "Original"}
        matrices = [("original", original, original_factors)]
        metrics, projections = [], []
        if compare:
            np.testing.assert_allclose(
                svd.project_onto_rank_one_directions(original, original_factors),
                original_sigma, rtol=svd.RTOL, atol=1e-10,
            )
        for quality in qualities:
            name = f"jpeg_q{quality}"
            labels[name] = f"JPEG Q={quality}"
            jpeg_path = output / f"{name}.jpg"
            decoded = imaging.jpeg_round_trip(pixels, jpeg_path, quality)
            decoded_name = f"{name}_decoded.png" if compare else "jpeg_decoded.png"
            imaging.save_display(decoded, output / decoded_name)
            matrices.append((name, decoded, svd.decompose(decoded)))
            mse, psnr = imaging.quality_metrics(original, decoded)
            metrics.append({
                "quality_factor": quality, "jpeg_bytes": jpeg_path.stat().st_size,
                "mse": mse, "psnr_db": psnr,
            })
            if compare:
                coefficients = svd.project_onto_rank_one_directions(decoded, original_factors)
                projections.extend({
                    "quality_factor": quality, "i": i, "original_sigma": sigma,
                    "coefficient": coefficient, "delta": coefficient - sigma,
                } for i, (sigma, coefficient) in enumerate(zip(original_sigma, coefficients), 1))
        error_rows, spectrum_rows = [], []
        validation = {}
        for name, matrix, factors in matrices:
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

        write_csv(output / "rank_errors.csv", error_rows)
        write_csv(output / "spectrum.csv", spectrum_rows)
        write_csv(output / "jpeg_metrics.csv", metrics)
        if compare:
            write_csv(output / "projections.csv", projections)
            charts.render_comparison(output)
        preview_quality = 80 if 80 in qualities else qualities[0]
        preview_name = f"jpeg_q{preview_quality}_decoded.png" if compare else "jpeg_decoded.png"
        charts.render(output, pixels, RANKS, labels, preview_quality, preview_name)
        manifest = {
            "status": "passed",
            "input": {"path": str(input_path), "sha256": sha256(payload).hexdigest(),
                      "shape": list(pixels.shape), "mode": "L"},
            "python": platform.python_version(),
            "platform": platform.platform(),
            "packages": {name: version(name) for name in ("numpy", "Pillow", "matplotlib")},
            "jpeg_library": features.version_codec("jpg"),
            "libjpeg_turbo": features.version_feature("libjpeg_turbo"),
            "jpeg_settings": (
                {"qualities": qualities, "optimize": False, "progressive": False}
                if compare else imaging.JPEG_SETTINGS
            ),
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
    parser.add_argument("--qualities", nargs="+", type=int, help="Enable JPEG comparison and projections")
    args = parser.parse_args()
    try:
        run(args.input, args.output_dir, args.qualities)
    except (ValueError, OSError, AssertionError, np.linalg.LinAlgError) as error:
        print(f"Experiment failed: {error}", file=sys.stderr)
        return 1
    print(f"Experiment passed: {args.output_dir / 'manifest.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
