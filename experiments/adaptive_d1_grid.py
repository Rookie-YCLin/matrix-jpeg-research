"""Exhaustive, reproducible integer-d1 baseline for adaptive SVD-QIM research.

This is intentionally an experiment wrapper, not a change to blind_watermark.
For every selected d1 it performs a fresh upstream embedding, measures PNG PSNR,
JPEG-encodes QF 5--10, and invokes the public blind bit extractor.
"""
from __future__ import annotations

import argparse
import csv
from dataclasses import asdict, dataclass
from hashlib import sha256
from importlib.metadata import distribution, version
import json
from pathlib import Path
import platform
import shutil
import tempfile
from time import perf_counter
from urllib.request import urlopen

import numpy as np
from PIL import Image, features

from experiments import ori_qf_scan as fixed
from experiments.svd_qim_psnr import rgb_psnr
from experiments.svd_qim_sweep import configured_instance, extract_with_qim


QFS = (5, 6, 7, 8, 9, 10)
D2 = 20
PSNR_THRESHOLD_DB = 40.0


@dataclass(frozen=True)
class Evaluation:
    d1: int
    qf: int
    errors: int
    total_bits: int
    ber: float
    extracted_bits: str
    png_psnr_db: float
    png_mse_rgb_8bit: float
    clean_errors: int
    embed_seconds: float
    jpeg_extract_seconds: float


def parse_d1_values(value: str) -> tuple[int, ...]:
    """Accept `1:150`, `1,4,8`, or a single positive integer."""
    if ":" in value:
        parts = value.split(":")
        if len(parts) != 2:
            raise argparse.ArgumentTypeError("range must be START:STOP")
        start, stop = (int(part) for part in parts)
        values = tuple(range(start, stop + 1))
    else:
        values = tuple(int(part) for part in value.split(","))
    if not values or any(d < 1 for d in values):
        raise argparse.ArgumentTypeError("d1 values must be positive integers")
    return tuple(sorted(set(values)))


def errors(expected: str, actual: str) -> int:
    if len(expected) != len(actual):
        raise ValueError("Blind extractor returned an unexpected bit length")
    return sum(a != b for a, b in zip(expected, actual))


def evaluate_d1(rgb: np.ndarray, d1: int, temp: Path) -> list[Evaluation]:
    """Evaluate a single d1 without retaining bulky marked/JPEG image files."""
    marked = temp / f"d1_{d1:03d}.png"
    started = perf_counter()
    wm = configured_instance(d1, D2)
    wm.read_img(img=fixed.to_bgr(rgb))
    wm.read_wm([int(bit) for bit in fixed.PAYLOAD], mode="bit")
    wm.embed(filename=str(marked))
    embed_seconds = perf_counter() - started
    marked_rgb = fixed.read_rgb(marked)
    png_mse, png_psnr = rgb_psnr(rgb, marked_rgb)
    clean_bits = extract_with_qim(marked_rgb, d1, D2)
    clean_errors = errors(fixed.PAYLOAD, clean_bits)

    rows: list[Evaluation] = []
    for qf in QFS:
        attacked = temp / f"d1_{d1:03d}_qf_{qf:02d}.jpg"
        started = perf_counter()
        with Image.open(marked) as image:
            image.save(attacked, format="JPEG", quality=qf, **fixed.JPEG)
        bits = extract_with_qim(fixed.read_rgb(attacked), d1, D2)
        elapsed = perf_counter() - started
        count = errors(fixed.PAYLOAD, bits)
        rows.append(Evaluation(
            d1=d1, qf=qf, errors=count, total_bits=fixed.WM_SIZE,
            ber=count / fixed.WM_SIZE, extracted_bits=bits,
            png_psnr_db=png_psnr, png_mse_rgb_8bit=png_mse,
            clean_errors=clean_errors,
            embed_seconds=embed_seconds, jpeg_extract_seconds=elapsed,
        ))
        attacked.unlink()
    marked.unlink()
    return rows


def summarise(rows: list[Evaluation]) -> list[dict[str, object]]:
    by_d1: dict[int, list[Evaluation]] = {}
    for row in rows:
        by_d1.setdefault(row.d1, []).append(row)
    result = []
    for d1, group in sorted(by_d1.items()):
        if tuple(row.qf for row in group) != QFS:
            raise AssertionError("Incomplete QF grid")
        mean_ber = float(np.mean([row.ber for row in group]))
        worst_ber = max(row.ber for row in group)
        psnr = group[0].png_psnr_db
        distortion = max(0.0, (PSNR_THRESHOLD_DB - psnr) / PSNR_THRESHOLD_DB)
        result.append({
            "d1": d1,
            "mean_ber": mean_ber,
            "worst_ber": worst_ber,
            "png_psnr_db": psnr,
            "png_mse_rgb_8bit": group[0].png_mse_rgb_8bit,
            "clean_errors": group[0].clean_errors,
            "model_a_feasible": group[0].clean_errors == 0 and worst_ber == 0.0 and psnr >= PSNR_THRESHOLD_DB,
            "model_b_lambda_0_5": 0.5 * mean_ber + 0.5 * distortion,
            "total_seconds": group[0].embed_seconds + sum(row.jpeg_extract_seconds for row in group),
        })
    return result


def write_svg(rows: list[Evaluation], summary: list[dict[str, object]], output: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    d1_values = [int(row["d1"]) for row in summary]
    figure, axis = plt.subplots(figsize=(8, 4.5))
    for qf in QFS:
        series = [row.ber for row in rows if row.qf == qf]
        axis.plot(d1_values, series, marker=".", linewidth=1, label=f"QF {qf}")
    axis.set(xlabel="integer d1", ylabel="BER", title="Blind BER versus d1", ylim=(-0.02, 1.02))
    axis.legend(ncol=3, fontsize=8)
    figure.tight_layout()
    figure.savefig(output / "ber_vs_d1.svg", format="svg")
    plt.close(figure)

    figure, axis = plt.subplots(figsize=(8, 4.5))
    axis.plot(d1_values, [float(row["png_psnr_db"]) for row in summary], marker=".")
    axis.axhline(PSNR_THRESHOLD_DB, color="red", linestyle="--", label="40 dB threshold")
    axis.set(xlabel="integer d1", ylabel="PNG PSNR (dB)", title="Embedding distortion versus d1")
    axis.legend()
    figure.tight_layout()
    figure.savefig(output / "psnr_vs_d1.svg", format="svg")
    plt.close(figure)

    figure, axis = plt.subplots(figsize=(6, 4.5))
    points = axis.scatter(
        [float(row["png_psnr_db"]) for row in summary],
        [float(row["worst_ber"]) for row in summary], c=d1_values, cmap="viridis", s=18,
    )
    axis.set(xlabel="PNG PSNR (dB)", ylabel="worst BER over QF5–10", title="d1 trade-off points")
    figure.colorbar(points, ax=axis, label="d1")
    figure.tight_layout()
    figure.savefig(output / "pareto_psnr_worst_ber.svg", format="svg")
    plt.close(figure)


def run(output: Path, d1_values: tuple[int, ...]) -> None:
    if output.exists():
        raise FileExistsError(f"Output must not already exist: {output}")
    provenance = json.loads(distribution("blind_watermark").read_text("direct_url.json"))
    if provenance.get("vcs_info", {}).get("commit_id") != fixed.UPSTREAM_COMMIT:
        raise RuntimeError("Unexpected blind_watermark source")
    with urlopen(fixed.SOURCE_URL.replace("/master/", f"/{fixed.UPSTREAM_COMMIT}/"), timeout=60) as response:
        source_bytes = response.read()
    if fixed.git_blob_sha(source_bytes) != fixed.SOURCE_BLOB_SHA:
        raise ValueError("Pinned source image blob mismatch")

    output.mkdir(parents=True)
    source = output / "ori_img.jpeg"
    source.write_bytes(source_bytes)
    rgb = fixed.read_rgb(source)
    config = {
        "experiment": "adaptive_d1_grid_phase2", "d1_values": list(d1_values), "d2": D2,
        "qfs": list(QFS), "psnr_threshold_db": PSNR_THRESHOLD_DB,
        "payload": fixed.PAYLOAD, "keys": fixed.KEYS, "jpeg": {"encoder": "Pillow", "format": "RGB", **fixed.JPEG},
        "upstream_commit": fixed.UPSTREAM_COMMIT, "source_blob_sha": fixed.SOURCE_BLOB_SHA,
        "source_sha256": sha256(source_bytes).hexdigest(), "source_shape_rgb": list(rgb.shape),
    }
    (output / "config.json").write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")

    temp = Path(tempfile.mkdtemp(prefix="adaptive-d1-", dir=output))
    try:
        rows = [row for d1 in d1_values for row in evaluate_d1(rgb, d1, temp)]
    finally:
        shutil.rmtree(temp, ignore_errors=True)
    summary = summarise(rows)
    with (output / "per_qf.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(asdict(rows[0])))
        writer.writeheader()
        writer.writerows(asdict(row) for row in rows)
    with (output / "per_d1.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(summary[0]))
        writer.writeheader()
        writer.writerows(summary)
    write_svg(rows, summary, output)
    feasible = [row for row in summary if bool(row["model_a_feasible"])]
    model_b = min(summary, key=lambda row: (float(row["model_b_lambda_0_5"]), int(row["d1"])))
    manifest = {
        **config, "status": "complete", "model_a": (
            {"status": "feasible", "d1": min(int(row["d1"]) for row in feasible)} if feasible
            else {"status": "infeasible", "domain": "integer d1 1..150 (or supplied grid)"}
        ),
        "model_b_lambda_0_5": model_b,
        "runtime_seconds": float(sum(float(row["total_seconds"]) for row in summary)),
        "python": platform.python_version(), "packages": {name: version(name) for name in ("blind_watermark", "numpy", "opencv-python", "PyWavelets", "Pillow", "matplotlib")},
        "pillow_jpeg": features.version("jpg"),
        "files_sha256": {path.name: fixed.sha256_file(path) for path in sorted(output.iterdir()) if path.is_file()},
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"model_a": manifest["model_a"], "model_b": model_b}, ensure_ascii=False))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--d1-values", type=parse_d1_values, default=tuple(range(1, 151)))
    args = parser.parse_args()
    run(args.output_dir, args.d1_values)


if __name__ == "__main__":
    main()
