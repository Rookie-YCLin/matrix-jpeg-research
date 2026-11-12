"""Validate the sparse-margin candidate on user-provided images.

This is an external generalization study.  It does not replace the project's
pinned single-image primary experiment.
"""
from __future__ import annotations

import argparse
import csv
from hashlib import sha256
import json
from pathlib import Path

import numpy as np
from PIL import Image

from experiments import ori_qf_scan as fixed
from experiments.paper_low_qf import decode, instance


QUALITIES = tuple(range(5, 100, 5))


def image_sha256(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def rgb(path: Path) -> np.ndarray:
    with Image.open(path) as im:
        if im.mode != "RGB":
            raise ValueError(f"{path.name} must be RGB, found {im.mode}")
        return np.asarray(im).copy()


def measure(expected: str, source: np.ndarray, artifact: Path, variant: str) -> dict:
    actual = decode(rgb(artifact), variant)
    errors = [i + 1 for i, (x, y) in enumerate(zip(expected, actual)) if x != y]
    pixels = rgb(artifact)
    mse = float(np.mean((source.astype(np.float64) - pixels.astype(np.float64)) ** 2))
    return {
        "errors": len(errors), "ber": len(errors) / len(expected),
        "extracted_bits": actual, "positions_1based": json.dumps(errors),
        "mse_rgb_8bit": mse, "psnr_db": 10 * np.log10(255 ** 2 / mse),
        "artifact_sha256": image_sha256(artifact),
    }


def run(input_dir: Path, output_dir: Path, qualities: tuple[int, ...], max_pixels: int | None, variants: tuple[str, ...]) -> None:
    images = sorted(input_dir.glob("*.jpg"))
    if not images:
        raise ValueError("No .jpg images found")
    output_dir.mkdir(parents=True, exist_ok=False)
    rows = []
    sources = []
    skipped = []
    for source_path in images:
        source = rgb(source_path)
        if max_pixels is not None and source.shape[0] * source.shape[1] > max_pixels:
            skipped.append({"name": source_path.name, "shape_rgb": list(source.shape), "reason": "exceeds_max_pixels"})
            continue
        source_id = source_path.stem
        sources.append({"name": source_path.name, "sha256": image_sha256(source_path), "shape_rgb": list(source.shape)})
        for variant in variants:
            variant_qualities = (5,) if variant == "g6" else qualities
            marked = output_dir / f"{source_id}_{variant}_marked.png"
            encoder = instance(variant)
            encoder.read_img(img=fixed.to_bgr(source))
            encoder.read_wm([int(b) for b in fixed.PAYLOAD], mode="bit")
            encoder.embed(filename=str(marked))
            for qf in (None, *variant_qualities):
                artifact = marked if qf is None else output_dir / f"{source_id}_{variant}_qf{qf:02d}.jpg"
                if qf is not None:
                    with Image.open(marked) as im:
                        im.save(artifact, format="JPEG", quality=qf, **fixed.JPEG)
                row = {
                    "source_name": source_path.name, "variant": variant,
                    "qf": "PNG" if qf is None else qf, "total_bits": len(fixed.PAYLOAD),
                    **measure(fixed.PAYLOAD, source, artifact, variant),
                }
                rows.append(row)
                print(f"{source_path.name} {variant} QF={row['qf']}: {row['errors']}/32", flush=True)
    with (output_dir / "results.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    manifest = {
        "scope": "external user-provided image validation; not the pinned primary image",
        "input_directory": str(input_dir), "sources": sources, "skipped_sources": skipped,
        "payload": fixed.PAYLOAD, "keys": fixed.KEYS, "jpeg": fixed.JPEG,
        "variants": list(variants),
        "qualities": list(qualities), "script_sha256": image_sha256(Path(__file__)),
        "files_sha256": {p.name: image_sha256(p) for p in output_dir.iterdir() if p.is_file()},
    }
    (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--qualities", nargs="+", type=int, default=QUALITIES)
    parser.add_argument("--max-pixels", type=int)
    parser.add_argument("--variants", nargs="+", default=["g6", "sparse_margin720"])
    arguments = parser.parse_args()
    if any(qf < 1 or qf > 100 for qf in arguments.qualities):
        raise ValueError("JPEG qualities must be in 1..100")
    run(arguments.input_dir, arguments.output_dir, tuple(arguments.qualities), arguments.max_pixels, tuple(arguments.variants))
