"""R1: rank-one block DCT energies and archived JPEG table-weighted scores."""
import argparse
import csv
from hashlib import sha256
from io import BytesIO
from pathlib import Path
import json
import os
import platform
import sys

import numpy as np
from PIL import Image, __version__ as pillow_version, features
import scipy
from scipy.fft import dct

from analysis.jpeg_tables import verified_table
from svd import decompose

BLOCK = 8
SHAPE = (512, 512)
ATOL = 1e-12
RTOL = 1e-8
PNG_SHA256 = "3b7cae537bc09699016556df746184a2376083244ae375a2740ee7157970ebf3"
# Frozen input identities from the reviewed M2 archive on origin/main.
JPEG_SHA256 = {
    40: "ac7861ba5ac9401226ae5f1a718d7894746f61e9f618e0a64009abfd9e33bba3",
    60: "8a17d29e7b0d438f9b73ccdf778f450b35e1ce268b8e07cfba259d2a58b368d8",
    80: "a6c0f1b9ff6de8330ba6ff302281636b45a7b1a274255f474ad7abff7dd6979b",
    95: "79a9a65e70922cf39b92aa11b5e44c2ca6025ebde53be621441c4a8fd3dc9667",
}


def block_dct(vectors):
    """Transform contiguous 8-sample blocks of each row vector."""
    vectors = np.asarray(vectors, dtype=np.float64)
    blocks = vectors.reshape(vectors.shape[0], -1, BLOCK)
    return dct(blocks, type=2, norm="ortho", axis=-1)


def energy_matrices(u_rows, v_rows):
    """One (vertical k, horizontal l) energy matrix per paired direction."""
    a = np.sum(block_dct(u_rows) ** 2, axis=1)
    b = np.sum(block_dct(v_rows) ** 2, axis=1)
    return a[:, :, None] * b[:, None, :]


def validate_energies(weights, count):
    if weights.shape != (count, BLOCK, BLOCK):
        raise ValueError(f"Unexpected W shape {weights.shape}")
    if not np.isfinite(weights).all() or np.any(weights < 0):
        raise ValueError("W contains a negative or non-finite entry")
    sums = weights.sum(axis=(1, 2))
    np.testing.assert_allclose(sums, np.ones(count), rtol=0, atol=ATOL)
    return float(np.max(np.abs(sums - 1.0)))


def sensitivity(weights, steps):
    return np.sqrt(np.sum(weights * np.asarray(steps, dtype=np.float64) ** 2, axis=(-2, -1)))


def read_fixed(path, digest):
    payload = path.read_bytes()
    if sha256(payload).hexdigest() != digest:
        raise ValueError(f"{path}: SHA-256 does not match the reviewed R1 input")
    return payload


def run(input_path, jpeg_dir, output):
    with Image.open(BytesIO(read_fixed(input_path, PNG_SHA256))) as image:
        if (image.format, image.mode, image.size) != ("PNG", "L", SHAPE[::-1]):
            raise ValueError("Expected the archived 512×512 8-bit grayscale PNG")
        original = np.asarray(image, dtype=np.float64)
    tables, jpeg_sources = {}, {}
    for q, digest in JPEG_SHA256.items():
        path = jpeg_dir / f"jpeg_q{q}.jpg"
        payload = read_fixed(path, digest)
        try:
            tables[q], evidence = verified_table(payload, SHAPE)
        except (ValueError, OSError, SyntaxError) as error:
            raise ValueError(f"{path}: {error}") from error
        jpeg_sources[str(q)] = {"path": path.as_posix(), "sha256": digest, **evidence}

    u, sigma, vh = decompose(original)
    weights = energy_matrices(u.T, vh)
    count = SHAPE[0]
    gap = validate_energies(weights, count)
    scores = {q: sensitivity(weights, steps) for q, steps in tables.items()}
    output.mkdir(parents=True, exist_ok=False)
    np.save(output / "weights.npy", weights, allow_pickle=False)
    with (output / "sensitivity.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(("i", "sigma_i", "Q", "S_i"))
        for i, value in enumerate(sigma, start=1):
            for q, values in scores.items():
                writer.writerow((i, float(value), q, float(values[i - 1])))
    manifest = {
        "status": "passed",
        "command": ["python", "-m", "analysis.r1", "--input", input_path.as_posix(),
                    "--jpeg-dir", jpeg_dir.as_posix(), "--output-dir", output.as_posix()],
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "numpy": np.__version__, "scipy": scipy.__version__, "pillow": pillow_version,
            "jpeg_codec": features.version_codec("jpg"),
            "libjpeg_turbo": features.version_feature("libjpeg_turbo"),
            "openblas_num_threads": os.environ.get("OPENBLAS_NUM_THREADS"),
        },
        "input": {"path": input_path.as_posix(), "sha256": PNG_SHA256, "shape": SHAPE, "mode": "L"},
        "jpeg_sources": jpeg_sources,
        "archived_encoding": {
            "manifest": "outputs/run-m2/manifest.json",
            "qualities": list(JPEG_SHA256), "optimize": False, "progressive": False,
            "pillow": "12.3.0", "jpeg_codec": "8.0", "libjpeg_turbo": "3.1.4.1",
        },
        "settings": {
            "dtype": "float64", "svd": "reduced", "block_size": BLOCK,
            "dct": "II", "norm": "ortho", "level_shift": False,
            "direction_index_base": 1, "frequency_index_base": 0,
        },
        "tolerances": {"weight_sum_atol": ATOL, "weight_sum_rtol": 0,
                       "replay_atol": ATOL, "replay_rtol": RTOL},
        "validation": {
            "directions_checked": count, "shape": list(weights.shape),
            "finite_and_nonnegative": True, "max_abs_weight_sum_error": gap,
            "raw_dqt_pillow_matches": len(tables), "score_rows": count * len(tables),
        },
        "artifacts": {
            "weights.npy": "float64 W, index [i-1, vertical k, horizontal l]",
            "sensitivity.csv": "one row per original direction i and JPEG Q",
        },
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--jpeg-dir", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    try:
        run(args.input, args.jpeg_dir, args.output_dir)
    except (ValueError, AssertionError, OSError) as error:
        parser.exit(1, f"R1 stopped: {error}\n")
    print(f"R1 PASS: {args.output_dir / 'manifest.json'}")


if __name__ == "__main__":
    main()
