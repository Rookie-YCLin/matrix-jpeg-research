"""Original blind_watermark BER versus JPEG quality (one pinned source image).

Run: python -m experiments.ori_qf_scan --output-dir outputs/ori-qf-scan
No candidate modifications and no PSNR metrics are computed.
"""
from __future__ import annotations

import argparse
import csv
from hashlib import sha1, sha256
from importlib.metadata import distribution, version
import json
from pathlib import Path
import platform
from urllib.request import urlopen
import warnings

import cv2
import numpy as np
from PIL import Image, features
from blind_watermark import WaterMark

SOURCE_URL = "https://raw.githubusercontent.com/guofei9987/blind_watermark/master/examples/pic/ori_img.jpeg"
SOURCE_BLOB_SHA = "ef48a056b3cab1d2c08723c014d8d515963f5a07"
UPSTREAM_COMMIT = "322c90dc02d45644692095b34d3a6b735b6edbd8"
QUALITIES = tuple(range(5, 100, 5))
PAYLOAD = "10110010111001000101101011010001"
WM_SIZE = len(PAYLOAD)
KEYS = {"password_img": 1, "password_wm": 1}
JPEG = {"subsampling": 0, "optimize": False, "progressive": False}


def git_blob_sha(payload: bytes) -> str:
    return sha1(f"blob {len(payload)}".encode("ascii") + bytes([0]) + payload).hexdigest()


def relative_reduction(base_errors: int, candidate_errors: int) -> float | None:
    """Percent relative reduction for equal positive bit denominators."""
    return None if base_errors == 0 else 100.0 * (base_errors - candidate_errors) / base_errors


def choose_worst_quality(rows: list[dict]) -> int:
    """Pick smallest QF among tied maximum baseline BER (not candidate-dependent)."""
    if not rows:
        raise ValueError("No JPEG measurements")
    maximum = max(int(row["error_count"]) for row in rows)
    return min(int(row["qf"]) for row in rows if int(row["error_count"]) == maximum)


def sha256_file(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def watermark_instance() -> WaterMark:
    wm = WaterMark(**KEYS, mode="common")
    core = wm.bwm_core
    if (core.d1, core.d2, core.fast_mode, tuple(core.block_shape)) != (36, 20, False, (4, 4)):
        raise RuntimeError("Pinned upstream SVD configuration differs from baseline")
    return wm


def to_bgr(rgb: np.ndarray) -> np.ndarray:
    return cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)


def extract_bits(rgb: np.ndarray) -> tuple[str, list[str]]:
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        extracted = np.asarray(watermark_instance().extract(
            embed_img=to_bgr(rgb), wm_shape=WM_SIZE, mode="bit"
        ))
    if extracted.shape != (WM_SIZE,) or not np.isin(extracted, [0, 1]).all():
        raise ValueError(f"Bad extracted bit vector: {extracted!r}")
    return "".join(str(int(bit)) for bit in extracted), [
        f"{w.category.__name__}: {w.message}" for w in caught
    ]


def read_rgb(path: Path) -> np.ndarray:
    with Image.open(path) as im:
        if im.mode != "RGB":
            raise ValueError(f"{path} must be RGB, is {im.mode}")
        return np.asarray(im).copy()


def make_row(qf: int | None, filename: Path, pixels: np.ndarray) -> dict:
    bits, notices = extract_bits(pixels)
    error_positions = [i + 1 for i, (a, b) in enumerate(zip(PAYLOAD, bits)) if a != b]
    return {
        "qf": "PNG" if qf is None else qf,
        "error_count": len(error_positions),
        "total_bits": WM_SIZE,
        "ber": len(error_positions) / WM_SIZE,
        "expected_bits": PAYLOAD,
        "extracted_bits": bits,
        "error_positions_1based": json.dumps(error_positions),
        "filename": filename.name,
        "sha256": sha256_file(filename),
        "warnings": json.dumps(notices, ensure_ascii=False),
    }


def run(output: Path) -> dict:
    provenance = json.loads(distribution("blind_watermark").read_text("direct_url.json"))
    observed_commit = provenance.get("vcs_info", {}).get("commit_id")
    if observed_commit != UPSTREAM_COMMIT:
        raise RuntimeError(f"Wrong blind_watermark upstream: {observed_commit}")

    output.mkdir(parents=True, exist_ok=False)
    with urlopen(SOURCE_URL, timeout=60) as response:
        source_bytes = response.read()
    if git_blob_sha(source_bytes) != SOURCE_BLOB_SHA:
        raise RuntimeError("Source image blob does not match the verified user-selected file")
    source = output / "ori_img.jpeg"
    source.write_bytes(source_bytes)
    rgb = read_rgb(source)
    mark_path = output / "marked.png"

    encoder = watermark_instance()
    encoder.read_img(img=to_bgr(rgb))
    block_rows, block_cols = encoder.bwm_core.ca_block_shape[:2]
    if int(block_rows) * int(block_cols) <= WM_SIZE:
        raise ValueError("Too few blocks to embed 32 watermark bits")
    encoder.read_wm([int(bit) for bit in PAYLOAD], mode="bit")
    encoder.embed(filename=str(mark_path))
    if not mark_path.is_file():
        raise RuntimeError("Upstream encoder failed to write marked.png")
    png_row = make_row(None, mark_path, read_rgb(mark_path))

    rows = []
    for qf in QUALITIES:
        attack = output / f"qf_{qf:02d}.jpg"
        with Image.open(mark_path) as img:
            img.save(attack, format="JPEG", quality=qf, **JPEG)
        row = make_row(qf, attack, read_rgb(attack))
        rows.append(row)
        print(f"QF={qf:02d}: errors={row['error_count']}/{WM_SIZE}, BER={row['ber']:.6f}", flush=True)

    x = choose_worst_quality(rows)
    peak = next(r for r in rows if r["qf"] == x)
    with (output / "results.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    with (output / "png_gate.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(png_row))
        writer.writeheader()
        writer.writerow(png_row)

    result = {
        "status": "complete" if png_row["error_count"] == 0 else "png_has_errors",
        "upstream_commit": UPSTREAM_COMMIT,
        "upstream_provenance": provenance,
        "source_url": SOURCE_URL,
        "source_git_blob_sha": SOURCE_BLOB_SHA,
        "source_sha256": sha256_file(source),
        "source_shape_rgb": list(rgb.shape),
        "source_dtype": str(rgb.dtype),
        "payload": PAYLOAD,
        "keys": KEYS,
        "watermark_length": WM_SIZE,
        "d1": 36,
        "d2": 20,
        "fast_mode": False,
        "jpeg": {"encoder": "Pillow", "format": "RGB", **JPEG, "qualities": QUALITIES},
        "python": platform.python_version(),
        "packages": {k: version(k) for k in ("blind_watermark", "opencv-python", "PyWavelets", "numpy", "Pillow")},
        "pillow_jpeg": features.version("jpg"),
        "opencv": cv2.__version__,
        "png_error_count": png_row["error_count"],
        "peak_qf": x,
        "peak_error_count": peak["error_count"],
        "peak_ber": peak["ber"],
        "peak_tie_qfs": [r["qf"] for r in rows if r["error_count"] == peak["error_count"]],
        "peak_rule": "Smallest QF among maximum baseline BER across QF=5,10,...,95",
        "relative_improvement_threshold_pass": 5,
        "relative_improvement_threshold_excellent": 10,
        "files": {f.name: sha256_file(f) for f in sorted(output.iterdir()) if f.is_file()},
    }
    (output / "manifest.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print("BASELINE_RESULT=" + json.dumps(
        {"x": x, "errors": peak["error_count"], "total_bits": WM_SIZE, "ber": peak["ber"],
         "tied_qfs": result["peak_tie_qfs"], "png_errors": png_row["error_count"]},
        ensure_ascii=False
    ), flush=True)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    run(args.output_dir)


if __name__ == "__main__":
    main()
