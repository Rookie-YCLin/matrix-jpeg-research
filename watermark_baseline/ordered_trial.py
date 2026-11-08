"""Paired zero-phase ordered embedding trial with the unchanged decoder."""
import argparse
import csv
from importlib.metadata import distribution, version
import json
from pathlib import Path
import platform

import cv2
import numpy as np
from PIL import features

from . import __main__ as w0
from . import mechanism, stress
from .ordered_embedding import new_embedder

PROTOCOL = "e7288807c917fe8a1b1aa59dd42b482c84c70a12"
QUALITIES = (10, 20, 30)
QUALITY_LIMITS = (0.5, 1.0)


def order_rows(image_id, method, stage, singular, bits, original=None):
    votes = mechanism.hard_votes(singular)
    for index, channel in enumerate(mechanism.CHANNELS):
        values = singular[index]
        row = {
            "image_id": image_id, "method": method, "stage": stage, "channel": channel,
            "blocks": len(values), "top_inversion": int(np.count_nonzero(values[:, 1] > values[:, 0])),
            "lower_inversion": int(np.count_nonzero(values[:, 1] < values[:, 2])),
            "negative_values": int(np.count_nonzero(values < 0)),
            "first_vote_errors": int(np.count_nonzero(votes[index, :, 0] != bits[index])),
            "second_vote_errors": int(np.count_nonzero(votes[index, :, 1] != bits[index])),
            "mean_squared_coefficient_change": None,
        }
        if original is not None:
            delta = values.astype(np.float64) - original[index]
            row["mean_squared_coefficient_change"] = float(np.mean(np.sum(delta**2, axis=1)))
        yield row


def pairs(results):
    original = {(row["image_id"], row["quality"]): row for row in results if row["method"] == "original"}
    for row in results:
        if row["method"] != "ordered":
            continue
        baseline = original[row["image_id"], row["quality"]]
        delta = row["psnr_marked_db"] - baseline["psnr_marked_db"]
        yield {
            "image_id": row["image_id"], "quality": row["quality"],
            "original_errors": baseline["error_count"], "ordered_errors": row["error_count"],
            "delta_ber": row["ber"] - baseline["ber"], "delta_png_psnr_db": delta,
            "within_0_5_db": abs(delta) <= QUALITY_LIMITS[0],
            "within_1_0_db": abs(delta) <= QUALITY_LIMITS[1],
            "delta_jpeg_psnr_db": None if row["quality"] is None else
            row["psnr_jpeg_vs_original_db"] - baseline["psnr_jpeg_vs_original_db"],
        }


def run(output):
    upstream_info = json.loads(distribution("blind_watermark").read_text("direct_url.json"))
    if upstream_info["vcs_info"]["commit_id"] != w0.UPSTREAM:
        raise ValueError("Unexpected upstream commit")
    baseline = mechanism.read_manifest(stress.BASELINE, stress.BASELINE_MANIFEST_SHA)
    mechanism.read_manifest(mechanism.JPEG_DIR, mechanism.JPEG_MANIFEST)
    refs = {}
    for directory in (stress.BASELINE, mechanism.JPEG_DIR):
        with (directory / "results.csv").open(newline="", encoding="utf-8") as stream:
            for row in csv.DictReader(stream):
                q = row["quality"]
                if (directory == stress.BASELINE and not q) or (
                    directory == mechanism.JPEG_DIR and q in ("10", "20", "30") and row["subsampling"] == "4:4:4"
                ):
                    refs[row["image_id"], q] = directory, row
    sources = stress.inputs(baseline)
    output.mkdir(parents=True, exist_ok=False)
    results, ordering, checks = [], [], []

    def check_reference(row):
        q = "" if row["quality"] is None else str(row["quality"])
        directory, reference = refs[row["image_id"], q]
        source = directory / reference["file"]
        if w0.digest(source) != reference["sha256"]:
            raise ValueError(f"Archive SHA-256 mismatch: {source}")
        if row["extracted_bits"] != reference["extracted_bits"]:
            raise ValueError(f"Original embedding failed to reproduce archived bits: {source}")
        for field in ("psnr_marked_db", "psnr_jpeg_vs_original_db"):
            if reference[field] and abs(row[field] - float(reference[field])) > 1e-10:
                raise ValueError(f"Original embedding failed to reproduce archived PSNR: {source}")
        checks.append({"file": row["file"], "reference": source.as_posix(),
                       "bit_and_psnr_match": True, "same_bytes": row["sha256"] == reference["sha256"]})

    manifest = {
        "status": "error", "protocol_commit": PROTOCOL,
        "command": ["python", "-m", "watermark_baseline.ordered_trial", "--output-dir", str(output)],
        "upstream": upstream_info, "python": platform.python_version(), "platform": platform.platform(),
        "packages": {name: version(name) for name in baseline["packages"]},
        "opencv": cv2.__version__, "pillow_jpeg": features.version("jpg"),
        "pillow_libjpeg_turbo": features.version_feature("libjpeg_turbo"),
        "baseline_manifest_sha256": stress.BASELINE_MANIFEST_SHA,
        "stress_manifest_sha256": mechanism.JPEG_MANIFEST,
        **{key: baseline[key] for key in ("inputs", "payload", "keys", "mode", "fast_mode",
                                           "d1", "d2", "block_shape", "decoder", "color", "psnr")},
        "jpeg": {"qualities": QUALITIES, "primary_quality": 10, "encoder": "Pillow RGB", **w0.JPEG},
        "png_psnr_limits_db": QUALITY_LIMITS, "phase": 0,
        "baseline_checks": checks, "no_attack_failures": [],
    }
    try:
        (output / "opencv-build.txt").write_text(cv2.getBuildInformation(), encoding="utf-8", newline="\n")
        for method, factory in (("original", w0.new_watermark), ("ordered", new_embedder)):
            for image_id, original_path, _ in sources:
                original = w0.load_rgb(original_path)
                embedded, s, quantized, immediate, bits, _ = mechanism.observe_embedding(original, factory)
                if method == "ordered" and (np.any(quantized < 0) or np.any(np.diff(quantized, axis=-1) > 0)):
                    raise ValueError("Ordered embedder emitted an invalid spectrum")
                png = output / f"{image_id}_{method}.png"
                ok, encoded = cv2.imencode(".png", embedded)
                if not ok:
                    raise OSError("OpenCV PNG encode failed")
                png.write_bytes(encoded.tobytes())
                marked = w0.load_rgb(png)
                marked_psnr = w0.psnr(original, marked)
                ordering.extend(order_rows(image_id, method, "quantized_index_order", quantized, bits, s))
                ordering.extend(order_rows(image_id, method, "reconstructed_sorted", immediate, bits))
                for q in (None, *QUALITIES):
                    file = png if q is None else output / f"{png.stem}_q{q}.jpg"
                    pixels = marked if q is None else stress.encode(png, file, q, 0)
                    row = w0.measure(image_id, original, marked_psnr, pixels, file, q)
                    row.update(method=method, source_png=png.name, source_png_sha256=w0.digest(png))
                    results.append(row)
                    stage = "PNG" if q is None else f"Q{q}"
                    spectra = mechanism.extract_spectra(w0.to_bgr(pixels))
                    ordering.extend(order_rows(image_id, method, stage, spectra, bits))
                    if q is None and (row["error_count"] or json.loads(row["warnings"])):
                        manifest["no_attack_failures"].append(row["file"])
                    if method == "original":
                        check_reference(row)
        stress.write_csv(output / "paired.csv", list(pairs(results)))
        manifest["status"] = "complete"
    except Exception as error:
        manifest["error"] = repr(error)
        raise
    finally:
        if results:
            stress.write_csv(output / "results.csv", results)
        if ordering:
            stress.write_csv(output / "ordering.csv", ordering)
        manifest["files"] = {path.name: w0.digest(path) for path in sorted(output.iterdir())}
        (output / "manifest.json").write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n"
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True, type=Path)
    run(parser.parse_args().output_dir)
