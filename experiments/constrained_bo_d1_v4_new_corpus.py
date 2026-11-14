"""Frozen public images unused in earlier CBO V1-V3.1 evaluations.

Exactly four distinct scikit-image 0.24.0 samples, not resized or derived
from an already evaluated source image. See V4 experiment specification.
"""
from __future__ import annotations

import argparse
import csv
from hashlib import sha256
from pathlib import Path

import numpy as np
from PIL import Image
from skimage import data

NAMES = ("colorwheel", "hubble_deep_field", "immunohistochemistry", "human_mitosis")
SOURCE = "https://scikit-image.org/docs/0.24.x/api/skimage.data.html"


def run(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    for name in NAMES:
        array = np.asarray(getattr(data, name)())
        if array.dtype != np.uint8:
            raise ValueError(f"Unexpected sample bit depth in {name}")
        if array.ndim == 2:
            array = np.repeat(array[:, :, None], 3, axis=2)
        if array.ndim != 3 or array.shape[2] != 3:
            raise ValueError(f"Unexpected sample shape for {name}: {array.shape}")
        destination = output_dir / f"{name}.png"
        Image.fromarray(array, mode="RGB").save(destination)
        rows.append({
            "name": name,
            "file": destination.name,
            "sha256": sha256(destination.read_bytes()).hexdigest(),
            "width": array.shape[1],
            "height": array.shape[0],
            "source": SOURCE,
            "note": "Original sample data; grayscale only expanded to RGB channels",
        })
    with (output_dir / "sources.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Saved {len(rows)} new sample images with SHA256 manifest")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    run(parser.parse_args().output_dir)
