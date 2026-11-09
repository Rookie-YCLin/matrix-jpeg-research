"""Fixed G6 d1=90, d2=20: JPEG QF 1..15 real BER diagnostic.

This is an isolated diagnostic, not a new watermark candidate. Image,
payload, password, JPEG settings, and upstream commit are pinned in the
existing experiments/ori_qf_scan.py module. A single marked PNG is reused
for all attacks; ground-truth bits never enter blind extraction.
"""
from __future__ import annotations

import csv
import json
from hashlib import sha256
from pathlib import Path
from argparse import ArgumentParser
from importlib.metadata import distribution, version
from urllib.request import urlopen

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image, features

from experiments import ori_qf_scan as fixed
from experiments.svd_qim_sweep import configured_instance, extract_with_qim

D1, D2 = 90, 20
QUALITY = tuple(range(1, 16))
CHECKPOINTS = {5: 32, 10: 0, 15: 0}


def save_csv(path, rows):
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader()
        w.writerows(rows)


def main():
    ap = ArgumentParser(description=__doc__)
    ap.add_argument("--output-dir", type=Path, required=True)
    out = ap.parse_args().output_dir
    out.mkdir(parents=True, exist_ok=False)

    provenance = json.loads(distribution("blind_watermark").read_text("direct_url.json"))
    commit = provenance.get("vcs_info", {}).get("commit_id")
    if commit != fixed.UPSTREAM_COMMIT:
        raise RuntimeError(f"Wrong upstream commit: {commit}")

    with urlopen(fixed.SOURCE_URL, timeout=60) as r:
        image_bytes = r.read()
    if fixed.git_blob_sha(image_bytes) != fixed.SOURCE_BLOB_SHA:
        raise RuntimeError("Image blob SHA mismatch")
    src = out / "ori_img.jpeg"
    src.write_bytes(image_bytes)
    image = fixed.read_rgb(src)

    marked = out / "primary_g6_marked.png"
    wm = configured_instance(D1, D2)
    wm.read_img(img=fixed.to_bgr(image))
    wm.read_wm([int(x) for x in fixed.PAYLOAD], mode="bit")
    wm.embed(filename=str(marked))
    marked_sha = fixed.sha256_file(marked)
    # Independently cross-check the already archived G6 marked PNG.
    archived_mark_sha = "d289b94ff41a4509fa363577b34e4a51026d834afa9dd4a3bcc6c1728d987541"
    if marked_sha != archived_mark_sha:
        raise RuntimeError("G6 marked PNG does not match archived experimental image")

    clean = extract_with_qim(fixed.read_rgb(marked), D1, D2)
    if clean != fixed.PAYLOAD:
        raise RuntimeError(f"Clean PNG extraction failed: {clean}")

    rows, bits_rows = [], []
    previous = None
    # Test the critical unknown QFs early; sort rows for the final curve.
    sequence = (5, 6, 7, 8, 9, 10, 15, 1, 2, 3, 4, 11, 12, 13, 14)
    for qf in sequence:
        attacked = out / f"g6_qf_{qf:02d}.jpg"
        with Image.open(marked) as img:
            img.save(attacked, format="JPEG", quality=qf, **fixed.JPEG)
        decoded = extract_with_qim(fixed.read_rgb(attacked), D1, D2)
        positions = [i + 1 for i, (a, b) in enumerate(zip(fixed.PAYLOAD, decoded)) if a != b]
        errors = len(positions)
        row = {
            "qf": qf, "d1": D1, "d2": D2, "errors": errors, "total_bits": fixed.WM_SIZE,
            "ber": errors / fixed.WM_SIZE,
            "ber_percent": 100 * errors / fixed.WM_SIZE,
            "all_bits_complement": errors == fixed.WM_SIZE,
            "expected_bits": fixed.PAYLOAD, "extracted_bits": decoded,
            "error_positions_1based": json.dumps(positions),
            "marked_sha256": marked_sha, "attack_sha256": fixed.sha256_file(attacked)
        }
        rows.append(row)
        bits_rows.extend({
            "qf": qf, "bit_position": i + 1, "expected": int(a),
            "decoded": int(b), "error": int(a != b),
        } for i, (a, b) in enumerate(zip(fixed.PAYLOAD, decoded)))
        print(f"G6_RESULT QF={qf:02d} errors={errors}/32 BER={100*errors/32:.4f}% decoded={decoded}", flush=True)
        # If we only get logs before the job completes, the critical range remains visible.

    rows.sort(key=lambda x: x["qf"])
    bits_rows.sort(key=lambda x: (x["qf"], x["bit_position"]))
    save_csv(out / "results.csv", rows)
    save_csv(out / "bits_by_qf.csv", bits_rows)

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot([x["qf"] for x in rows], [x["ber_percent"] for x in rows], marker="o")
    ax.set_xticks(QUALITY)
    ax.set_ylim(-5, 105)
    ax.set_xlabel("JPEG QF")
    ax.set_ylabel("BER (%)")
    ax.set_title("Fixed G6 (d1=90, d2=20) | JPEG QF=1..15 | 32 bits")
    ax.grid(alpha=.3)
    for x in rows:
        ax.annotate(f'{x["errors"]}/32', (x["qf"], x["ber_percent"]),
                    xytext=(0, 7), textcoords="offset points",
                    ha="center", fontsize=7)
    fig.tight_layout()
    fig.savefig(out / "ber_qf_1_15.png", dpi=180)
    plt.close(fig)

    checkpoints = {
        qf: next(x["errors"] for x in rows if x["qf"] == qf)
        for qf in CHECKPOINTS
    }
    mismatches = {q: {"expected": CHECKPOINTS[q], "measured": v}
                  for q, v in checkpoints.items() if v != CHECKPOINTS[q]}
    info = {
        "status": "pass" if not mismatches else "checkpoint_mismatch",
        "upstream_commit": commit, "source_sha256": sha256(image_bytes).hexdigest(),
        "source_blob_sha": fixed.SOURCE_BLOB_SHA,
        "marked_sha256": marked_sha, "payload": fixed.PAYLOAD,
        "d1": D1, "d2": D2, "jpeg": {"quality": list(QUALITY), **fixed.JPEG},
        "pillow_jpeg": features.version("jpg"),
        "versions": {x: version(x) for x in ("numpy", "Pillow", "blind_watermark")},
        "checkpoints": checkpoints, "checkpoint_mismatches": mismatches,
        "mean_error_bits_across_qf": sum(x["errors"] for x in rows) / len(rows),
    }
    (out / "manifest.json").write_text(
        json.dumps(info, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print("G6_COMPLETE_RESULTS=" + json.dumps([
        {"qf": r["qf"], "errors": r["errors"], "ber_percent": r["ber_percent"]}
        for r in rows
    ]), flush=True)
    if mismatches:
        raise RuntimeError(f"Archived checkpoint mismatch: {mismatches}")


if __name__ == "__main__":
    main()
