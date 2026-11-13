"""Prepare 12 independent public sample images from scikit-image.

This produces unmodified image arrays as RGB PNG and a source manifest.
No resized/cropped variants are counted as independent images.
"""
import argparse
import csv
import hashlib
from pathlib import Path

import numpy as np
from PIL import Image
from skimage import data

NAMES = ("astronaut", "camera", "chelsea", "coffee", "coins", "moon",
         "clock", "page", "text", "rocket", "brick", "grass")
SOURCE = "https://scikit-image.org/docs/stable/api/skimage.data"

def run(output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    for name in NAMES:
        arr = getattr(data, name)()
        if arr.ndim == 2:
            arr = np.repeat(arr[:, :, None], 3, axis=2)
        if arr.ndim != 3 or arr.shape[2] != 3:
            raise ValueError(f"Unexpected channels: {name}")
        image = Image.fromarray(np.asarray(arr, dtype=np.uint8), "RGB")
        target = output_dir / f"{name}.png"
        image.save(target)
        rows.append({
            "name": name, "file": target.name,
            "sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
            "width": image.width, "height": image.height,
            "source": SOURCE,
            "note": "Original scikit-image sample; verify per-image reuse terms in docs",
        })
    with (output_dir / "sources.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0])
        writer.writeheader()
        writer.writerows(rows)
    print(f"Saved {len(rows)} source images and provenance manifest")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    run(args.output_dir)
