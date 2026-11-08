"""Reproduce only the two fixed G6 QF15 arms and measure RGB PSNR."""
import argparse
import csv
from hashlib import sha256
from importlib.metadata import distribution, version
import json
from math import inf, log10
from pathlib import Path
import platform
from urllib.request import urlopen

import numpy as np

SOURCE_SHA256 = "17bed8cfeb5534351d2f35d4addd9407e0c0132132444276a0f826c7ae9923c2"
QF = 15
ARMS = {"upstream": (36, 20), "svd_step_90": (90, 20)}
STAGES = ("uncompressed_embedded", "qf15_attacked")
ARCHIVE = Path(__file__).resolve().parents[1] / "outputs/svd-qim-qf15-selected/results.csv"


def rgb_psnr(reference, image):
    """Return RGB uint8 MSE and PSNR using a 255 peak and float64 arithmetic."""
    if (reference.shape != image.shape or reference.ndim != 3
            or reference.shape[-1] != 3 or not reference.size):
        raise ValueError("Expected matching non-empty H×W×3 RGB images")
    if reference.dtype != np.uint8 or image.dtype != np.uint8:
        raise ValueError("Expected uint8 RGB images")
    delta = reference.astype(np.float64) - image.astype(np.float64)
    mse = float(np.mean(delta**2))
    return mse, inf if mse == 0 else 10 * log10(255**2 / mse)


def run(output):
    import cv2
    from PIL import Image, features

    from experiments import ori_qf_scan as fixed
    from experiments.svd_qim_sweep import configured_instance, extract_with_qim

    provenance = json.loads(distribution("blind_watermark").read_text("direct_url.json"))
    if provenance.get("vcs_info", {}).get("commit_id") != fixed.UPSTREAM_COMMIT:
        raise RuntimeError("Unexpected upstream commit")
    source_url = fixed.SOURCE_URL.replace("/master/", f"/{fixed.UPSTREAM_COMMIT}/")
    with urlopen(source_url, timeout=60) as response:
        data = response.read()
    if fixed.git_blob_sha(data) != fixed.SOURCE_BLOB_SHA or sha256(data).hexdigest() != SOURCE_SHA256:
        raise ValueError("Platelet source hash mismatch")

    output.mkdir(parents=True, exist_ok=False)
    source = output / "ori_img.jpeg"
    source.write_bytes(data)
    rgb = fixed.read_rgb(source)
    if rgb.shape != (1108, 738, 3):
        raise ValueError(f"Unexpected platelet dimensions: {rgb.shape}")
    with ARCHIVE.open(newline="", encoding="utf-8") as stream:
        archived = {row["variant"]: row for row in csv.DictReader(stream)
                    if row["payload"] == "primary" and row["qf"] == str(QF)}

    rows = []
    for variant, (d1, d2) in ARMS.items():
        marked = output / f"{variant}_marked.png"
        attacked = output / f"{variant}_qf15.jpg"
        wm = configured_instance(d1, d2)
        wm.read_img(img=fixed.to_bgr(rgb))
        wm.read_wm([int(bit) for bit in fixed.PAYLOAD], mode="bit")
        # Same OpenCV PNG encoder and default parameters as upstream imwrite.
        # Writing bytes with pathlib also supports Unicode Windows paths.
        ok, png_bytes = cv2.imencode(".png", wm.embed())
        if not ok:
            raise OSError("OpenCV could not encode embedded PNG")
        marked.write_bytes(png_bytes.tobytes())
        with Image.open(marked) as png:
            png.save(attacked, format="JPEG", quality=QF, **fixed.JPEG)
        for stage, path in zip(STAGES, (marked, attacked)):
            pixels = fixed.read_rgb(path)
            mse, psnr = rgb_psnr(rgb, pixels)
            bits = extract_with_qim(pixels, d1, d2)
            errors = sum(a != b for a, b in zip(fixed.PAYLOAD, bits))
            reference = archived[variant]
            hash_column = "marked_sha256" if stage == STAGES[0] else "attack_sha256"
            digest = fixed.sha256_file(path)
            rows.append({
                "variant": variant, "d1": d1, "d2": d2, "stage": stage,
                "mse_rgb_8bit": mse, "psnr_db": psnr,
                "extracted_bits": bits, "errors": errors, "total_bits": fixed.WM_SIZE,
                "ber": errors / fixed.WM_SIZE,
                "archived_bits_match": bits == (fixed.PAYLOAD if stage == STAGES[0] else reference["extracted_bits"]),
                "file": path.name, "sha256": digest, "archived_sha256_match": digest == reference[hash_column],
            })
    for original, g6 in zip(rows[:2], rows[2:]):
        delta = g6["psnr_db"] - original["psnr_db"]
        for row in (original, g6):
            row["delta_g6_minus_upstream_db"] = None if np.isnan(delta) else delta
    results = output / "results.csv"
    with results.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    manifest = {
        "command": ["python", "-m", "experiments.svd_qim_psnr", "--output-dir", str(output)],
        "source_url": source_url, "source_blob": fixed.SOURCE_BLOB_SHA, "source_sha256": SOURCE_SHA256,
        "source_shape_rgb": list(rgb.shape), "reference": "Pillow RGB uint8 decode of ori_img.jpeg",
        "mse": "Mean squared float64 difference over all H×W×3 entries", "peak": 255,
        "upstream": provenance, "arms": ARMS, "payload": fixed.PAYLOAD, "keys": fixed.KEYS,
        "mode": "common", "fast_mode": False, "block_shape": [4, 4],
        "jpeg": {"encoder": "Pillow", "quality": QF, **fixed.JPEG},
        "python": platform.python_version(), "platform": platform.platform(),
        "packages": {name: version(name) for name in ("blind_watermark", "numpy", "opencv-python",
                                                      "PyWavelets", "Pillow")},
        "opencv": cv2.__version__, "pillow_jpeg": features.version("jpg"),
        "pillow_libjpeg_turbo": features.version_feature("libjpeg_turbo"),
        "archived_ber_csv_sha256": fixed.sha256_file(ARCHIVE),
        "files_sha256": {p.name: fixed.sha256_file(p) for p in sorted(output.iterdir())},
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8", newline="\n")
    if not all(row["archived_bits_match"] for row in rows):
        raise RuntimeError("QF15 or clean BER differs from archive; inspect saved results")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True, type=Path)
    run(parser.parse_args().output_dir)
