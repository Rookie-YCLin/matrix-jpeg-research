"""W0-D: independent JPEG stress attacks on the archived W0 marked PNGs."""
import argparse
import csv
from importlib.metadata import distribution, version
import json
from pathlib import Path
import platform
import warnings

import cv2
import numpy as np
from PIL import Image, features
from blind_watermark.bwm_core import one_dim_kmeans

from . import __main__ as w0

BASELINE = Path("outputs/run-w0")
BASELINE_COMMIT = "f5a47fc1ba40cc35f5794648b4440cb1fed782d1"
BASELINE_MANIFEST_SHA = "2b2f3be7a14044d7b3b5a241df91db23907a97774c643a4fb66565163df06cd3"
ATTACKS = (
    ("A", 10, 0), ("A", 20, 0), ("A", 30, 0),
    ("B", 40, 2), ("B", 60, 2), ("B", 80, 2),
)
SAMPLING = {0: "4:4:4", 2: "4:2:0"}


def encode(marked_png, target, quality, sampling):
    with Image.open(marked_png) as image:
        image.save(target, format="JPEG", quality=quality, **(w0.JPEG | {"subsampling": sampling}))
    return w0.load_rgb(target)


def decision_scores(pixels, *, d2=20):
    decoder = w0.configured_watermark(d2)
    decoder.wm_size = w0.BIT_COUNT
    raw = decoder.bwm_core.extract(img=w0.to_bgr(pixels), wm_shape=w0.BIT_COUNT)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        labels = one_dim_kmeans(raw)
    scores = decoder.extract_decrypt(raw.copy())
    labels = decoder.extract_decrypt(labels.copy())
    bits = "".join(str(int(bit)) for bit in labels)
    low, high = scores[~labels], scores[labels]
    if not low.size or not high.size:
        return scores, bits, None, None, [str(item.message) for item in caught]

    # The final labels bound a separating threshold. Use the midpoint of the
    # final cluster means as a proxy for distance, only if it preserves labels.
    gap = float(high.min() - low.max())
    midpoint = float((low.mean() + high.mean()) / 2)
    if not np.array_equal(scores > midpoint, labels):
        midpoint = None
    return scores, bits, midpoint, gap, [str(item.message) for item in caught]


def inputs(baseline):
    sources = []
    for entry in baseline["inputs"]["images"]:
        image_id = entry["id"]
        original = w0.INPUTS / entry["file"]
        marked = BASELINE / f"{image_id}_marked.png"
        if w0.digest(original) != entry["sha256"] or w0.digest(marked) != baseline["files"][marked.name]:
            raise ValueError(f"W0 source hash mismatch for {image_id}")
        sources.append((image_id, original, marked))
    return sources


def write_csv(path, rows):
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def run(output):
    provenance = json.loads(distribution("blind_watermark").read_text("direct_url.json"))
    if provenance["vcs_info"]["commit_id"] != w0.UPSTREAM:
        raise RuntimeError("Installed upstream commit differs from W0")
    baseline_path = BASELINE / "manifest.json"
    if w0.digest(baseline_path) != BASELINE_MANIFEST_SHA:
        raise ValueError("Archived W0 manifest differs from the pinned PR #13 baseline")
    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    sources = inputs(baseline)
    output.mkdir(parents=True, exist_ok=False)

    results, decisions = [], []
    for image_id, original_path, marked_path in sources:
        original = w0.load_rgb(original_path)
        marked_psnr = w0.psnr(original, w0.load_rgb(marked_path))
        for group, quality, sampling in ATTACKS:
            target = output / f"{image_id}_{group}_q{quality}.jpg"
            pixels = encode(marked_path, target, quality, sampling)
            result = w0.measure(image_id, original, marked_psnr, pixels, target, quality)
            result.update(group=group, subsampling=SAMPLING[sampling], pillow_subsampling=sampling,
                          source_png=marked_path.name, source_png_sha256=baseline["files"][marked_path.name])
            results.append(result)

            scores, bits, midpoint, gap, notices = decision_scores(pixels)
            if bits != result["extracted_bits"]:
                raise RuntimeError(f"Diagnostic decisions diverged from public bit API: {target}")
            for index, (score, bit) in enumerate(zip(scores, bits), 1):
                decisions.append({
                    "image_id": image_id, "group": group, "quality": quality,
                    "subsampling": SAMPLING[sampling], "position_1based": index,
                    "score": score, "cluster_bit": bit, "centroid_midpoint": midpoint,
                    "signed_margin_to_midpoint": None if midpoint is None else score - midpoint,
                    "cluster_gap": gap, "diagnostic_warnings": json.dumps(notices),
                })

    write_csv(output / "results.csv", results)
    write_csv(output / "decision_scores.csv", decisions)
    (output / "opencv-build.txt").write_text(cv2.getBuildInformation(), encoding="utf-8", newline="\n")
    manifest = {
        "status": "complete",
        "command": ["python", "-m", "watermark_baseline.stress", "--output-dir", str(output)],
        "baseline_commit": BASELINE_COMMIT,
        "baseline_manifest_sha256": BASELINE_MANIFEST_SHA,
        "inputs": baseline["inputs"],
        "marked_pngs": {marked.name: baseline["files"][marked.name] for _, _, marked in sources},
        "upstream": provenance,
        "python": platform.python_version(), "platform": platform.platform(),
        "packages": {name: version(name) for name in baseline["packages"]},
        "opencv": cv2.__version__, "pillow_jpeg": features.version("jpg"),
        "pillow_libjpeg_turbo": features.version_feature("libjpeg_turbo"),
        **{key: baseline[key] for key in (
            "payload", "keys", "mode", "fast_mode", "d1", "d2", "block_shape", "decoder",
            "color", "psnr", "blocks_per_channel"
        )},
        "jpeg": {
            "encoder": "Pillow RGB", "optimize": w0.JPEG["optimize"],
            "progressive": w0.JPEG["progressive"],
            "conditions": [{"group": group, "quality": q, "subsampling": SAMPLING[s],
                            "pillow_subsampling": s} for group, q, s in ATTACKS],
        },
        "scores": "Separate upstream core.extract + one_dim_kmeans + extract_decrypt. "
                  "Midpoint of final cluster means, stored only if it reproduces labels. "
                  "Gap = minimum high score minus maximum low score.",
        "files": {path.name: w0.digest(path) for path in sorted(output.iterdir())},
    }
    (output / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True, type=Path)
    run(parser.parse_args().output_dir)
