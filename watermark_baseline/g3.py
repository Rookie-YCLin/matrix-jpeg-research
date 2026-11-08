"""Compare the two G3 decoders on the same archived PNG/JPEG pixels."""
import argparse
import csv
from importlib.metadata import distribution, version
import json
from pathlib import Path
import platform
import warnings

from blind_watermark.bwm_core import one_dim_kmeans
import cv2
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from PIL import features

from . import __main__ as w0
from . import stress
from .soft_decision import new_decoder

FORMULA_COMMIT = "318eed431eca0d106805d0b1fa05dc5110272ea8"
STRESS_COMMIT = "168e5070cacbdeeaefab58ed469dd7e90db4aa3f"
STRESS_DIR = Path("outputs/run-w0-d")
STRESS_SHA = "6ae88428a147467a7dc6d6025966fe7f994632013ecf0f61ffeed04ecad4c238"
CONDITIONS = ("PNG", "Q10", "Q20", "Q30")
METHODS = ("hard", "soft")


def read_csv(path):
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def extract(bgr, method):
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        labels = new_decoder(method).extract(embed_img=bgr, wm_shape=w0.BIT_COUNT, mode="bit")
    if labels.shape != (w0.BIT_COUNT,) or labels.dtype != np.bool_:
        raise ValueError("Unexpected upstream bit result")
    return "".join(str(int(bit)) for bit in labels), [str(w.message) for w in caught]


def diagnostic(bgr, method):
    decoder = new_decoder(method)
    decoder.wm_size = w0.BIT_COUNT
    raw = decoder.bwm_core.extract(img=bgr, wm_shape=w0.BIT_COUNT)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        labels = one_dim_kmeans(raw)
    scores = decoder.extract_decrypt(raw.copy())
    labels = decoder.extract_decrypt(labels.copy())
    low, high = scores[~labels], scores[labels]
    midpoint = gap = None
    if low.size and high.size:
        gap = float(high.min() - low.max())
        candidate = float((low.mean() + high.mean()) / 2)
        if np.array_equal(scores > candidate, labels):
            midpoint = candidate
    return scores, "".join(str(int(bit)) for bit in labels), midpoint, gap, [str(w.message) for w in caught]


def archived_inputs():
    selected = {}
    manifests = []
    for directory, expected in ((stress.BASELINE, stress.BASELINE_MANIFEST_SHA), (STRESS_DIR, STRESS_SHA)):
        path = directory / "manifest.json"
        if w0.digest(path) != expected:
            raise ValueError(f"Historical manifest hash mismatch: {path}")
        manifest = json.loads(path.read_text(encoding="utf-8"))
        manifests.append(manifest)
        csv_path = directory / "results.csv"
        if w0.digest(csv_path) != manifest["files"]["results.csv"]:
            raise ValueError(f"Historical results hash mismatch: {csv_path}")
        for row in read_csv(csv_path):
            q = row["quality"]
            if directory == stress.BASELINE:
                if q:
                    continue
                condition = "PNG"
            else:
                if q not in ("10", "20", "30") or row["subsampling"] != "4:4:4":
                    continue
                condition = f"Q{q}"
            path = directory / row["file"]
            if w0.digest(path) != row["sha256"] or row["sha256"] != manifest["files"][path.name]:
                raise ValueError(f"Historical image hash mismatch: {path}")
            selected[row["image_id"], condition] = (path, row)
    sources = stress.inputs(manifests[0])
    if set(selected) != {(image_id, condition) for image_id, _, _ in sources for condition in CONDITIONS}:
        raise ValueError("Missing or unexpected archived conditions")
    return selected, sources, manifests[0]


def plot(output):
    summary = read_csv(output / "summary.csv")
    scores = read_csv(output / "decision_scores.csv")
    fig, (ber, polarity) = plt.subplots(1, 2, figsize=(10, 4), layout="constrained")
    colors = {"hard": "#375885", "soft": "#a14b27"}
    for i, method in enumerate(METHODS):
        rows = [row for row in summary if row["method"] == method]
        bars = ber.bar(np.arange(4) + (i - 0.5) * 0.32,
                       [float(row["ber"]) * 100 for row in rows], width=0.32,
                       label=method, color=colors[method])
        ber.bar_label(bars, labels=[row["error_count"] for row in rows], padding=3, fontsize=8)
    ber.set(xticks=range(4), xticklabels=CONDITIONS, ylim=(0, 100),
            ylabel="BER (%)", title="Same input files · errors out of 96")
    ber.legend()
    for i, image_id in enumerate(("astronaut", "chelsea", "coffee")):
        for j, method in enumerate(METHODS):
            rows = [r for r in scores if (r["image_id"], r["condition"], r["method"]) == (image_id, "Q20", method)]
            for bit, marker in (("0", "o"), ("1", "x")):
                y = i + (j - 0.5) * 0.30 + (int(bit) - 0.5) * 0.12
                values = [float(r["score"]) for r in rows if r["original_bit"] == bit]
                polarity.scatter(values, [y] * len(values), color=colors[method], marker=marker, s=18,
                                 alpha=0.65, label=f"{method} · bit {bit}" if i == 0 else None)
    polarity.set(yticks=range(3), yticklabels=("astronaut", "chelsea", "coffee"),
                 xlabel="Aggregated score", title="Q20 · scores by original bit (post hoc)")
    polarity.legend(fontsize=7)
    fig.savefig(output / "comparison.png", dpi=160)
    plt.close(fig)


def run(output):
    provenance = json.loads(distribution("blind_watermark").read_text("direct_url.json"))
    if provenance["vcs_info"]["commit_id"] != w0.UPSTREAM:
        raise ValueError("Unexpected upstream commit")
    selected, sources, baseline = archived_inputs()
    output.mkdir(parents=True, exist_ok=False)
    results, decisions = [], []
    for image_id, original_path, _ in sources:
        original = w0.load_rgb(original_path)
        for condition in CONDITIONS:
            path, reference = selected[image_id, condition]
            rgb = w0.load_rgb(path)
            bgr = w0.to_bgr(rgb)
            psnr = w0.psnr(original, rgb)
            historical_psnr = reference["psnr_jpeg_vs_original_db"] or reference["psnr_marked_db"]
            if abs(psnr - float(historical_psnr)) > 1e-10 or reference["original_bits"] != w0.PAYLOAD:
                raise ValueError(f"Historical PSNR or payload mismatch: {path}")
            for method in METHODS:
                recovered, notices = extract(bgr, method)
                scores, labels, midpoint, gap, diagnostic_notices = diagnostic(bgr, method)
                if recovered != labels:
                    raise ValueError(f"Independent diagnostic disagrees: {path} ({method})")
                if method == "hard" and recovered != reference["extracted_bits"]:
                    raise ValueError(f"Original decoder disagrees with the archive: {path}")
                positions, ber = w0.compare_bits(w0.PAYLOAD, recovered)
                means = [float(scores[[b == bit for b in w0.PAYLOAD]].mean()) for bit in "01"]
                keys = {"image_id": image_id, "condition": condition, "method": method}
                results.append({
                    **keys, "subsampling": "" if condition == "PNG" else "4:4:4",
                    "input_path": path.as_posix(), "input_sha256": reference["sha256"],
                    "psnr_vs_original_db": psnr, "original_bits": w0.PAYLOAD, "extracted_bits": recovered,
                    "error_positions_1based": json.dumps(positions), "error_count": len(positions),
                    "total_bits": w0.BIT_COUNT, "ber": ber, "mean_score_true_0": means[0],
                    "mean_score_true_1": means[1], "score_order_reversed": means[0] > means[1],
                    "all_bits_flipped": len(positions) == w0.BIT_COUNT,
                    "cluster_gap": gap, "centroid_midpoint": midpoint,
                    "warnings": json.dumps(notices + diagnostic_notices),
                })
                for i, (score, bit, original_bit) in enumerate(zip(scores, labels, w0.PAYLOAD), 1):
                    decisions.append({**keys, "position_1based": i, "score": score,
                                      "cluster_bit": bit, "original_bit": original_bit})
    summary = []
    for condition in CONDITIONS:
        for method in METHODS:
            rows = [row for row in results if (row["condition"], row["method"]) == (condition, method)]
            errors = sum(row["error_count"] for row in rows)
            total = sum(row["total_bits"] for row in rows)
            summary.append({"condition": condition, "method": method, "error_count": errors,
                            "total_bits": total, "ber": errors / total})

    for name, rows in (("results", results), ("decision_scores", decisions), ("summary", summary)):
        stress.write_csv(output / f"{name}.csv", rows)
    plot(output)
    (output / "opencv-build.txt").write_text(cv2.getBuildInformation(), encoding="utf-8", newline="\n")
    manifest = {
        "status": "complete", "command": ["python", "-m", "watermark_baseline.g3", "--output-dir", str(output)],
        "formula_commit": FORMULA_COMMIT, "formula": "g(r)=(1-sin(2*pi*r))/2; v=(3*g(r0)+g(r1))/4",
        "w0_commit": stress.BASELINE_COMMIT, "w0_manifest_sha256": stress.BASELINE_MANIFEST_SHA,
        "w0_d_commit": STRESS_COMMIT, "w0_d_manifest_sha256": STRESS_SHA,
        "upstream": provenance, "python": platform.python_version(), "platform": platform.platform(),
        "packages": {name: version(name) for name in (*baseline["packages"], "matplotlib")},
        "opencv": cv2.__version__, "pillow_jpeg": features.version("jpg"),
        "pillow_libjpeg_turbo": features.version_feature("libjpeg_turbo"),
        **{key: baseline[key] for key in ("inputs", "payload", "keys", "mode", "fast_mode",
                                           "d1", "d2", "block_shape", "decoder", "color", "psnr")},
        "conditions": CONDITIONS, "sampling": "4:4:4", "archive_only": True,
        "images": {path.as_posix(): ref["sha256"] for path, ref in selected.values()},
        "historical_hard_rows_verified": len(selected),
        "files": {path.name: w0.digest(path) for path in sorted(output.iterdir())},
    }
    (output / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True, type=Path)
    run(parser.parse_args().output_dir)
