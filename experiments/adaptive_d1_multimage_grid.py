"""Cross-image measured d1 oracle collection with resumable per-image CSVs.

Run in the pinned blind_watermark environment; calls the real embed/JPEG/extract
pipeline from experiments.adaptive_d1_grid. No synthetic BER is generated.

Example:
 python -m experiments.adaptive_d1_multimage_grid \
   --input-dir data/evaluation_images --output-dir outputs/multimage-qf5-10 \
   --d1-start 1 --d1-stop 150
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
import tempfile

import numpy as np
from PIL import Image

from experiments.adaptive_d1_grid import evaluate_d1, summarise

EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}


def source_images(folder: Path) -> list[Path]:
    if not folder.is_dir():
        raise NotADirectoryError(folder)
    return sorted(p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in EXTENSIONS)


def run(input_dir: Path, output_dir: Path, d1_start: int, d1_stop: int) -> None:
    if not 1 <= d1_start <= d1_stop:
        raise ValueError("Require 1 <= d1_start <= d1_stop")
    images = source_images(input_dir)
    if not images:
        raise ValueError("No source images")
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = output_dir / "manifest.jsonl"
    for index, image_path in enumerate(images):
        raw = image_path.read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        image_dir = output_dir / f"{index:04d}_{digest[:16]}"
        image_dir.mkdir(exist_ok=True)
        meta_path = image_dir / "source.json"
        identity = {
            "source_filename": image_path.name,
            "source_sha256": digest,
            "d1_start": d1_start,
            "d1_stop": d1_stop,
            "qf": [5, 6, 7, 8, 9, 10],
            "d2": 20,
            "status": "in_progress",
        }
        if meta_path.exists():
            previous = json.loads(meta_path.read_text(encoding="utf-8"))
            for field in ("source_sha256", "d1_start", "d1_stop", "qf", "d2"):
                if previous[field] != identity[field]:
                    raise RuntimeError(f"Resume configuration mismatch: {image_dir} {field}")
        else:
            meta_path.write_text(json.dumps(identity, indent=2) + "\n", encoding="utf-8")
        rows_path = image_dir / "per_d1.csv"
        existing = {}
        if rows_path.exists():
            with rows_path.open(newline="", encoding="utf-8") as stream:
                for row in csv.DictReader(stream):
                    existing[int(row["d1"])] = row
        with Image.open(image_path) as im:
            rgb = np.asarray(im.convert("RGB"), dtype=np.uint8)
        with tempfile.TemporaryDirectory(prefix="d1-real-jpeg-") as tmp:
            for d in range(d1_start, d1_stop + 1):
                if d in existing:
                    continue
                measured = summarise(evaluate_d1(rgb, d, Path(tmp)))[0]
                existing[d] = measured
                tmp_path = rows_path.with_suffix(".csv.tmp")
                with tmp_path.open("w", newline="", encoding="utf-8") as stream:
                    writer = csv.DictWriter(stream, fieldnames=list(measured))
                    writer.writeheader()
                    for key in sorted(existing):
                        writer.writerow(existing[key])
                tmp_path.replace(rows_path)
        complete = len(existing) == d1_stop - d1_start + 1
        identity["status"] = "complete" if complete else "partial"
        identity["evaluations"] = len(existing)
        identity["width"] = int(rgb.shape[1])
        identity["height"] = int(rgb.shape[0])
        if complete:
            ordered = [existing[d] for d in range(d1_start, d1_stop + 1)]
            best = min(ordered, key=lambda row: (float(row["model_b_lambda_0_5"]), int(row["d1"])))
            identity["model_b_best_d1"] = int(best["d1"])
            identity["model_b_best_objective"] = float(best["model_b_lambda_0_5"])
            identity["model_a_feasible"] = any(
                str(row["model_a_feasible"]).lower() == "true" for row in ordered
            )
        meta_path.write_text(json.dumps(identity, indent=2) + "\n", encoding="utf-8")
        with manifest_path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(identity, ensure_ascii=False) + "\n")
        print(f'{image_path.name}: {identity["status"]}, {len(existing)} d1 evaluations', flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--d1-start", type=int, default=1)
    parser.add_argument("--d1-stop", type=int, default=150)
    args = parser.parse_args()
    run(args.input_dir, args.output_dir, args.d1_start, args.d1_stop)


if __name__ == "__main__":
    main()
