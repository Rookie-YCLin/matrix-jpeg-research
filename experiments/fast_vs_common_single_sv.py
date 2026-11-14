"""Compare first-singular-value-only QIM in common and fast modes.

The same upstream package, source, payload, JPEG encoder, and passwords are
used. fast_mode alone changes whether DCT coefficients are shuffled before SVD.
"""
from __future__ import annotations

import argparse
import csv
import json
from hashlib import sha256
from pathlib import Path
from statistics import median
from time import perf_counter
from urllib.request import urlopen

import cv2
import numpy as np
from PIL import Image

from experiments import ori_qf_scan as fixed
from experiments.svd_qim_psnr import rgb_psnr

ARMS = (
    ("common_d36", False, 36),
    ("fast_d36", True, 36),
    ("common_d90", False, 90),
    ("fast_d90", True, 90),
)
QFS = (5, 10, 15, 20, 25, 50, 95)
REPEATS = 3


def instance(fast: bool, d1: int):
    wm = fixed.watermark_instance()
    wm.bwm_core.d1 = d1
    wm.bwm_core.d2 = 0
    wm.bwm_core.fast_mode = fast
    assert wm.bwm_core.fast_mode == fast and wm.bwm_core.d2 == 0
    return wm


def embed(rgb: np.ndarray, fast: bool, d1: int) -> np.ndarray:
    wm = instance(fast, d1)
    wm.read_img(img=fixed.to_bgr(rgb))
    wm.read_wm([int(bit) for bit in fixed.PAYLOAD], mode="bit")
    return wm.embed()


def decode(rgb: np.ndarray, fast: bool, d1: int) -> str:
    wm = instance(fast, d1)
    bits = np.asarray(wm.extract(embed_img=fixed.to_bgr(rgb), wm_shape=32, mode="bit"))
    if bits.shape != (32,) or not np.isin(bits, (0, 1)).all():
        raise RuntimeError(f"Invalid blind extraction: {bits!r}")
    return "".join(map(lambda bit: str(int(bit)), bits))


def main(out: Path) -> None:
    out.mkdir(parents=True, exist_ok=False)
    with urlopen(fixed.SOURCE_URL, timeout=90) as stream:
        original_bytes = stream.read()
    if fixed.git_blob_sha(original_bytes) != fixed.SOURCE_BLOB_SHA:
        raise ValueError("Pinned input image changed")
    source = out / "source.jpeg"
    source.write_bytes(original_bytes)
    original = fixed.read_rgb(source)
    rows = []
    timings = []
    for name, fast, d1 in ARMS:
        embed_times = []
        for _ in range(REPEATS):
            start = perf_counter()
            result = embed(original, fast, d1)
            embed_times.append(perf_counter() - start)
        marked_path = out / f"{name}.png"
        if not cv2.imwrite(str(marked_path), result):
            raise IOError(f"Writing marked image failed: {marked_path}")
        marked_rgb = fixed.read_rgb(marked_path)
        extract_times = []
        for _ in range(REPEATS):
            start = perf_counter()
            clean_bits = decode(marked_rgb, fast, d1)
            extract_times.append(perf_counter() - start)
        timings.append({
            "arm": name, "mode": "fast" if fast else "common", "d1": d1, "d2": 0,
            "embed_seconds_median": median(embed_times),
            "extract_seconds_median": median(extract_times),
            "embed_seconds_samples": embed_times,
            "extract_seconds_samples": extract_times,
        })
        for qf in (None, *QFS):
            if qf is None:
                attack_rgb = marked_rgb
                qf_label = "PNG"
            else:
                attack_path = out / f"{name}_qf{qf:02d}.jpg"
                with Image.open(marked_path) as image:
                    image.save(attack_path, format="JPEG", quality=qf, **fixed.JPEG)
                attack_rgb = fixed.read_rgb(attack_path)
                qf_label = str(qf)
            decoded = decode(attack_rgb, fast, d1)
            errors = sum(x != y for x, y in zip(fixed.PAYLOAD, decoded))
            mse, psnr = rgb_psnr(original, attack_rgb)
            row = {
                "arm": name, "mode": "fast" if fast else "common", "d1": d1, "d2": 0,
                "qf": qf_label, "errors": errors, "total": fixed.WM_SIZE,
                "ber": errors / fixed.WM_SIZE, "psnr_db": psnr, "mse": mse,
                "decoded_bits": decoded,
            }
            rows.append(row)
            print("RESULT " + json.dumps(row), flush=True)
        print("TIMING " + json.dumps(timings[-1]), flush=True)
    for fn, data in (("results.csv", rows), ("timing.csv", [
        {k: v for k, v in row.items() if not k.endswith("_samples")} for row in timings
    ])):
        with (out / fn).open("w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=list(data[0]))
            writer.writeheader()
            writer.writerows(data)
    manifest = {
        "status": "complete", "source_sha256": sha256(original_bytes).hexdigest(),
        "source_blob": fixed.SOURCE_BLOB_SHA, "upstream_commit": fixed.UPSTREAM_COMMIT,
        "payload": fixed.PAYLOAD, "passwords": fixed.KEYS,
        "modes": "common versus fast", "d2": 0, "qfs": QFS, "timing_repeats": REPEATS,
        "jpeg": fixed.JPEG, "results": rows, "timings": timings
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print("SUMMARY: COMPLETE", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    main(parser.parse_args().output_dir)
