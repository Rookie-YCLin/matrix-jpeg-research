"""Extract image-only features for an adaptive-d1 predictor; no watermark is embedded."""
from __future__ import annotations

import argparse
import csv
from hashlib import sha256
import json
from pathlib import Path

import cv2
import numpy as np
import pywt
from PIL import Image


def sha256_file(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def features(path: Path) -> dict[str, object]:
    with Image.open(path) as image:
        rgb = np.asarray(image.convert("RGB"), dtype=np.float64)
    gray = cv2.cvtColor(rgb.astype(np.uint8), cv2.COLOR_RGB2GRAY).astype(np.float64)
    gx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3); gy = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
    gradient = np.hypot(gx, gy)
    ll, (lh, hl, hh) = pywt.dwt2(gray, "haar")
    dwt_total = sum(float(np.sum(x**2)) for x in (ll, lh, hl, hh))
    # OpenCV's DCT implementation requires even dimensions.  Discard at most
    # one trailing row/column solely for this whole-image feature.
    dct_input = gray[:gray.shape[0] - gray.shape[0] % 2, :gray.shape[1] - gray.shape[1] % 2] / 255.0
    dct = cv2.dct(dct_input); h, w = dct.shape; low = dct[:max(1, h // 8), :max(1, w // 8)]
    dct_total = float(np.sum(dct**2)); low_energy = float(np.sum(low**2))
    # Fixed non-overlapping 4x4 blocks mirror the watermark's SVD block scale.
    crop = gray[: gray.shape[0] // 4 * 4, : gray.shape[1] // 4 * 4]
    blocks = crop.reshape(crop.shape[0] // 4, 4, crop.shape[1] // 4, 4).transpose(0, 2, 1, 3).reshape(-1, 4, 4)
    spectra = np.linalg.svd(np.asarray([cv2.dct(block / 255.0) for block in blocks]), compute_uv=False)
    ratio = spectra[:, 0] / np.maximum(spectra[:, 1], 1e-12)
    return {
        "image": path.name, "sha256": sha256_file(path), "width": rgb.shape[1], "height": rgb.shape[0],
        "gray_mean": float(gray.mean()), "gray_variance": float(gray.var()),
        "gradient_mean": float(gradient.mean()), "gradient_variance": float(gradient.var()),
        "dwt_ll_energy_fraction": float(np.sum(ll**2) / dwt_total),
        "dwt_detail_energy_fraction": float((np.sum(lh**2) + np.sum(hl**2) + np.sum(hh**2)) / dwt_total),
        "dct_low_energy_fraction": low_energy / dct_total,
        "dct_high_energy_fraction": 1.0 - low_energy / dct_total,
        "svd_sigma1_mean": float(spectra[:, 0].mean()), "svd_sigma1_std": float(spectra[:, 0].std()),
        "svd_sigma1_sigma2_ratio_mean": float(ratio.mean()),
        "svd_decay_mean": float(np.mean(spectra[:, 1] / np.maximum(spectra[:, 0], 1e-12))),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    if args.output_dir.exists(): raise FileExistsError(args.output_dir)
    paths = sorted(path for path in args.input_dir.iterdir() if path.suffix.lower() in {".jpg", ".jpeg", ".png"})
    if not paths: raise ValueError("No JPEG/PNG inputs")
    args.output_dir.mkdir(parents=True)
    rows = [features(path) for path in paths]
    with (args.output_dir / "features.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    (args.output_dir / "config.json").write_text(json.dumps({"input_count": len(paths), "source_directory": str(args.input_dir), "features": list(rows[0]), "status": "features_only_no_d1_labels"}, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__": main()
