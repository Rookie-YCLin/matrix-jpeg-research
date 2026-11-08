"""Exploratory SVD QIM step sweep at pre-registered worst JPEG QF=15.

Changes are restricted to the two singular-value quantizer periods and their
matching blind SVD extraction periods. Everything else remains upstream.
All attempted candidates and controls are recorded; no truth-based decoding.
"""
from __future__ import annotations

import argparse
import csv
from hashlib import sha256
from importlib.metadata import distribution
import json
from pathlib import Path
from urllib.request import urlopen

import numpy as np
from PIL import Image

from experiments import ori_qf_scan as fixed

# Pre-defined SVD QIM step candidates. Controls include the exact original pair.
CANDIDATES = (
    (36, 20), (36, 0), (48, 0), (48, 20), (48, 30),
    (60, 0), (60, 20), (60, 30), (72, 0), (72, 20),
    (72, 40), (90, 0), (90, 20), (96, 40), (108, 20),
)
SECONDARY_QF = (10, 20, 25)
BASELINE_QF15_ERRORS = 32


def configured_instance(d1: int, d2: int):
    wm = fixed.watermark_instance()
    wm.bwm_core.d1, wm.bwm_core.d2 = d1, d2
    return wm


def extract_with_qim(image: np.ndarray, d1: int, d2: int) -> str:
    wm = configured_instance(d1, d2)
    raw = np.asarray(wm.extract(embed_img=fixed.to_bgr(image), wm_shape=fixed.WM_SIZE, mode="bit"))
    if raw.shape != (fixed.WM_SIZE,) or not np.isin(raw, [0, 1]).all():
        raise AssertionError("Public blind extraction did not return 32 bits")
    return "".join(str(int(x)) for x in raw)


def observed_error(expected: str, received: str) -> int:
    return sum(x != y for x, y in zip(expected, received))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    out = args.output_dir
    out.mkdir(parents=True, exist_ok=False)

    provenance = json.loads(distribution("blind_watermark").read_text("direct_url.json"))
    if provenance.get("vcs_info", {}).get("commit_id") != fixed.UPSTREAM_COMMIT:
        raise RuntimeError("Upstream commit mismatch")
    with urlopen(fixed.SOURCE_URL, timeout=60) as src:
        original_bytes = src.read()
    if fixed.git_blob_sha(original_bytes) != fixed.SOURCE_BLOB_SHA:
        raise ValueError("Source image mismatch")
    original_path = out / "ori_img.jpeg"
    original_path.write_bytes(original_bytes)
    original = fixed.read_rgb(original_path)

    rows = []
    for d1, d2 in CANDIDATES:
        run_id = f"svd_d1_{d1:03d}_d2_{d2:03d}"
        marked = out / f"{run_id}.png"
        wm = configured_instance(d1, d2)
        wm.read_img(img=fixed.to_bgr(original))
        wm.read_wm([int(b) for b in fixed.PAYLOAD], mode="bit")
        wm.embed(filename=str(marked))
        marked_pixels = fixed.read_rgb(marked)
        clean_bits = extract_with_qim(marked_pixels, d1, d2)
        clean_errors = observed_error(fixed.PAYLOAD, clean_bits)

        for qf in (15, *SECONDARY_QF):
            attacked = out / f"{run_id}_qf_{qf:02d}.jpg"
            with Image.open(marked) as image:
                image.save(attacked, format="JPEG", quality=qf, **fixed.JPEG)
            bits = extract_with_qim(fixed.read_rgb(attacked), d1, d2)
            nerr = observed_error(fixed.PAYLOAD, bits)
            row = {
                "run_id": run_id, "d1": d1, "d2": d2, "qf": qf,
                "errors": nerr, "total_bits": fixed.WM_SIZE,
                "ber": nerr / fixed.WM_SIZE,
                "relative_reduction_vs_qf15_baseline": (
                    fixed.relative_reduction(BASELINE_QF15_ERRORS, nerr) if qf == 15 else ""
                ),
                "clean_errors": clean_errors, "extracted_bits": bits,
                "error_positions_1based": json.dumps([
                    i + 1 for i, (expected, actual) in
                    enumerate(zip(fixed.PAYLOAD, bits)) if expected != actual
                ]),
                "marked_sha256": fixed.sha256_file(marked),
                "attacked_sha256": fixed.sha256_file(attacked),
            }
            rows.append(row)
            print(f"RESULT {run_id} QF={qf} errors={nerr}/32 clean={clean_errors}", flush=True)

    path = out / "results.csv"
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    best_q15 = sorted(
        (r for r in rows if r["qf"] == 15 and r["clean_errors"] == 0),
        key=lambda r: (r["errors"], r["d1"], r["d2"]),
    )
    manifest = {
        "status": "complete",
        "upstream_commit": fixed.UPSTREAM_COMMIT,
        "source_blob_sha": fixed.SOURCE_BLOB_SHA,
        "source_sha256": sha256(original_bytes).hexdigest(),
        "qf_primary": 15,
        "baseline_errors": BASELINE_QF15_ERRORS,
        "payload": fixed.PAYLOAD,
        "jpeg": fixed.JPEG,
        "candidate_design": "Change only two SVD QIM quantization periods, retain original floor grid and blind extraction rule",
        "all_candidates": CANDIDATES,
        "secondary_qf": SECONDARY_QF,
        "best_zero_png_errors": (
            {"d1": best_q15[0]["d1"], "d2": best_q15[0]["d2"],
             "qf15_errors": best_q15[0]["errors"],
             "relative_reduction_percent": best_q15[0]["relative_reduction_vs_qf15_baseline"]}
            if best_q15 else None
        ),
        "files_sha256": {p.name: fixed.sha256_file(p) for p in sorted(out.iterdir()) if p.is_file()},
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print("CANDIDATE_SUMMARY=" + json.dumps(manifest["best_zero_png_errors"]), flush=True)


if __name__ == "__main__":
    main()
