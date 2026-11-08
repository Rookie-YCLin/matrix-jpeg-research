"""Run the fixed W0 experiment using the upstream public bit API."""
import argparse
import csv
from hashlib import sha256
from importlib.metadata import distribution, version
import json
from math import inf, log10
from pathlib import Path
import platform
import sys
import warnings

import cv2
import numpy as np
from PIL import Image, features
from blind_watermark import WaterMark

UPSTREAM = "322c90dc02d45644692095b34d3a6b735b6edbd8"
INPUTS = Path("data/w0")
PAYLOAD = "10110010111001000101101011010001"
BIT_COUNT = 32
QUALITIES = (40, 60, 80, 95)
KEYS = {"password_img": 1, "password_wm": 1}
JPEG = {"subsampling": 0, "optimize": False, "progressive": False}


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def load_rgb(path):
    with Image.open(path) as image:
        if image.mode != "RGB":
            raise ValueError(f"{path}: expected RGB, got {image.mode}")
        return np.array(image)


def to_bgr(rgb):
    return cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)


def new_watermark():
    watermark = WaterMark(**KEYS, mode="common")
    core = watermark.bwm_core
    if (core.d1, core.d2, core.fast_mode, tuple(core.block_shape)) != (36, 20, False, (4, 4)):
        raise RuntimeError("Unexpected upstream defaults")
    return watermark


def configured_watermark(d2):
    if d2 not in (10, 20, 30):
        raise ValueError(f"Unsupported d2: {d2}")
    watermark = new_watermark()
    watermark.bwm_core.d2 = d2
    return watermark


def embed(rgb, target, *, d2=20):
    watermark = configured_watermark(d2)
    watermark.read_img(img=to_bgr(rgb))
    height, width = watermark.bwm_core.ca_block_shape[:2]
    if height * width <= BIT_COUNT:
        raise ValueError("Upstream requires strictly more blocks per channel than payload bits")
    watermark.read_wm([int(bit) for bit in PAYLOAD], mode="bit")
    watermark.embed(filename=str(target))
    if not target.is_file():
        raise OSError(f"Upstream PNG writer did not create {target}")
    return int(height * width)


def extract(rgb, *, d2=20):
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        bits = np.asarray(
            configured_watermark(d2).extract(embed_img=to_bgr(rgb), wm_shape=BIT_COUNT, mode="bit")
        )
    if bits.shape != (BIT_COUNT,) or not np.isin(bits, [0, 1]).all():
        raise ValueError(f"Invalid upstream bit result: {bits!r}")
    return "".join(str(int(bit)) for bit in bits), [
        f"{item.category.__name__}: {item.message}" for item in caught
    ]


def compare_bits(expected, recovered):
    if len(expected) != BIT_COUNT or len(recovered) != BIT_COUNT:
        raise ValueError("Expected two complete 32-bit payloads")
    positions = [i for i, (a, b) in enumerate(zip(expected, recovered), 1) if a != b]
    return positions, len(positions) / BIT_COUNT


def psnr(reference, pixels):
    if reference.shape != pixels.shape:
        raise ValueError("PSNR requires matching image dimensions and channels")
    mse = np.mean((reference.astype(np.float64) - pixels.astype(np.float64)) ** 2)
    return inf if mse == 0 else 10 * log10(255**2 / mse)


def encode_attack(marked_png, target, quality):
    with Image.open(marked_png) as image:
        image.save(target, format="JPEG", quality=quality, **JPEG)
    return load_rgb(target)


def measure(image_id, original, marked_psnr, pixels, path, quality=None, *, d2=20):
    recovered, notices = extract(pixels, d2=d2)
    positions, ber = compare_bits(PAYLOAD, recovered)
    return {
        "image_id": image_id, "attack": "none" if quality is None else "jpeg",
        "quality": quality, "d1": 36, "d2": d2, "original_bits": PAYLOAD,
        "extracted_bits": recovered, "error_positions_1based": json.dumps(positions),
        "error_count": len(positions), "total_bits": BIT_COUNT, "ber": ber,
        "psnr_marked_db": marked_psnr,
        "psnr_jpeg_vs_original_db": None if quality is None else psnr(original, pixels),
        "file": path.name, "bytes": path.stat().st_size, "sha256": digest(path),
        "warnings": json.dumps(notices, ensure_ascii=False),
    }


def run(output):
    provenance = json.loads(distribution("blind_watermark").read_text("direct_url.json"))
    if provenance.get("vcs_info", {}).get("commit_id") != UPSTREAM:
        raise RuntimeError("Installed blind_watermark does not match the fixed commit")
    source = json.loads((INPUTS / "inputs.json").read_text(encoding="utf-8"))
    originals = {}
    for entry in source["images"]:
        path = INPUTS / entry["file"]
        if digest(path) != entry["sha256"]:
            raise ValueError(f"Input SHA-256 mismatch: {path}")
        rgb = load_rgb(path)
        if rgb.shape != (*reversed(entry["size"]), 3) or rgb.dtype != np.uint8:
            raise ValueError(f"Input dimensions or dtype mismatch: {path}")
        originals[entry["id"]] = rgb

    output.mkdir(parents=True, exist_ok=False)
    (output / "opencv-build.txt").write_text(
        cv2.getBuildInformation(), encoding="utf-8", newline="\n"
    )
    packages = {
        name: version(name)
        for name in ("blind_watermark", "opencv-python", "PyWavelets", "numpy", "Pillow", "pytest")
    }
    manifest = {
        "command": ["python", "-m", "watermark_baseline", "--output-dir", str(output)],
        "inputs": source, "upstream": provenance, "python": platform.python_version(),
        "platform": platform.platform(), "packages": packages,
        "opencv": cv2.__version__, "pillow_jpeg": features.version("jpg"),
        "pillow_libjpeg_turbo": features.version_feature("libjpeg_turbo"),
        "payload": PAYLOAD, "keys": KEYS, "mode": "common", "fast_mode": False,
        "d1": 36, "d2": 20, "block_shape": [4, 4],
        "decoder": "WaterMark.extract(mode=bit), upstream 1D k-means + bit unshuffle",
        "color": "Pillow RGB uint8 -> OpenCV BGR uint8 -> upstream float32 YUV",
        "jpeg": {"encoder": "Pillow RGB", "qualities": QUALITIES, **JPEG},
        "psnr": {"peak": 255, "dtype": "float64", "reference": "original RGB"},
        "blocks_per_channel": {},
    }
    rows = []
    status = "error"
    try:
        for image_id, original in originals.items():
            marked = output / f"{image_id}_marked.png"
            manifest["blocks_per_channel"][image_id] = embed(original, marked)
            pixels = load_rgb(marked)
            rows.append(measure(image_id, original, psnr(original, pixels), pixels, marked))

        if any(row["error_count"] or json.loads(row["warnings"]) for row in rows):
            status = "png_gate_failed"
            return False

        for row in rows.copy():
            image_id = row["image_id"]
            marked = output / row["file"]
            for quality in QUALITIES:
                target = output / f"{image_id}_q{quality}.jpg"
                pixels = encode_attack(marked, target, quality)
                rows.append(measure(image_id, originals[image_id], row["psnr_marked_db"],
                                    pixels, target, quality))
        status = "complete"
        return True
    except Exception as error:
        manifest["error"] = repr(error)
        raise
    finally:
        if rows:
            with (output / "results.csv").open("w", encoding="utf-8", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
                writer.writeheader()
                writer.writerows(rows)
        manifest["status"] = status
        manifest["files"] = {path.name: digest(path) for path in sorted(output.iterdir())}
        (output / "manifest.json").write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8", newline="\n",
        )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    if not run(args.output_dir):
        sys.exit("PNG gate failed. Inspect the saved results.csv and manifest.json.")


if __name__ == "__main__":
    main()
