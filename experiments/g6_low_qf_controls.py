"""Follow-up controls for unexpected G6 BER inversion at JPEG QF5–7.

Checks 1) independent 32-bit payloads, 2) absence-of-watermark control,
and 3) sign and separation of pre-KMeans raw bit scores.

All comparisons use the pinned image / same JPEG settings as original G6.
"""
from __future__ import annotations

from argparse import ArgumentParser
from pathlib import Path
from urllib.request import urlopen
import csv
import json
import numpy as np
from PIL import Image

from experiments import ori_qf_scan as fixed
from experiments.svd_qim_sweep import configured_instance, extract_with_qim
from experiments.svd_qim_validation import PAYLOADS

D1, D2 = 90, 20
QFS = (1, 4, 5, 6, 7, 8, 9, 10)
MARKED = ("primary", "holdout", "complement")


def scores_and_bits(image):
    instance = configured_instance(D1, D2)
    instance.wm_size = fixed.WM_SIZE
    raw_scores = instance.bwm_core.extract(img=fixed.to_bgr(image), wm_shape=fixed.WM_SIZE)
    aligned = np.asarray(instance.extract_decrypt(wm_avg=np.array(raw_scores, copy=True)), dtype=float)
    bits = extract_with_qim(image, D1, D2)
    return aligned, bits


def write_csv(path, rows):
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0])
        writer.writeheader()
        writer.writerows(rows)


def main():
    ap = ArgumentParser()
    ap.add_argument("--output-dir", type=Path, required=True)
    output = ap.parse_args().output_dir
    output.mkdir(parents=True, exist_ok=False)

    with urlopen(fixed.SOURCE_URL, timeout=60) as response:
        original_bytes = response.read()
    if fixed.git_blob_sha(original_bytes) != fixed.SOURCE_BLOB_SHA:
        raise RuntimeError("Source image changed")
    original_path = output / "ori_img.jpeg"
    original_path.write_bytes(original_bytes)
    original_rgb = fixed.read_rgb(original_path)

    rows = []
    for case in (*MARKED, "unmarked"):
        expected = PAYLOADS["primary"] if case == "unmarked" else PAYLOADS[case]
        if case == "unmarked":
            source = original_path
        else:
            source = output / f"{case}_g6_marked.png"
            wm = configured_instance(D1, D2)
            wm.read_img(img=fixed.to_bgr(original_rgb))
            wm.read_wm([int(x) for x in expected], mode="bit")
            wm.embed(filename=str(source))
            # Critical: controls must have zero error before the JPEG attack.
            _, clean = scores_and_bits(fixed.read_rgb(source))
            if clean != expected:
                raise RuntimeError(f"Clean extraction failure in case={case}")
        for qf in QFS:
            attacked = output / f"{case}_qf{qf:02d}.jpg"
            with Image.open(source) as image:
                image.save(attacked, "JPEG", quality=qf, **fixed.JPEG)
            aligned, bits = scores_and_bits(fixed.read_rgb(attacked))
            zero = aligned[[k == "0" for k in expected]]
            one = aligned[[k == "1" for k in expected]]
            nerr = sum(a != b for a, b in zip(expected, bits))
            row = {
                "case": case, "qf": qf, "errors": nerr, "ber_percent": nerr / 32 * 100,
                "all_bits_complement": nerr == 32,
                "mean_score_for_expected_zero": float(np.mean(zero)),
                "mean_score_for_expected_one": float(np.mean(one)),
                "mean_score_gap_one_minus_zero": float(np.mean(one) - np.mean(zero)),
                "max_score_expected_zero": float(np.max(zero)),
                "min_score_expected_one": float(np.min(one)),
                "expected": expected, "decoded": bits,
            }
            rows.append(row)
            print(
                f"CONTROL case={case} QF={qf:02d} errors={nerr}/32 "
                f"mean_gap_1_minus_0={row['mean_score_gap_one_minus_zero']:.6f} "
                f"zero_max={row['max_score_expected_zero']:.6f} "
                f"one_min={row['min_score_expected_one']:.6f}",
                flush=True,
            )
    write_csv(output / "controls.csv", rows)
    (output / "manifest.json").write_text(
        json.dumps({"d1": D1, "d2": D2, "qfs": QFS, "cases": (*MARKED, "unmarked"),
                    "jpeg": fixed.JPEG, "source_sha": fixed.sha256_file(original_path)},
                   indent=2) + "\n", encoding="utf-8")
    print("CONTROL_SUMMARY=" + json.dumps([
        {"case": r["case"], "qf": r["qf"], "errors": r["errors"],
         "score_gap": round(r["mean_score_gap_one_minus_zero"], 5)}
        for r in rows
    ]), flush=True)


if __name__ == "__main__":
    main()
