"""G2 paired comparison of upstream d2 settings."""
import argparse
import csv
from importlib.metadata import distribution, version
import json
from pathlib import Path
import platform

import cv2
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import features

from . import __main__ as w0
from . import stress

SETTINGS = (20, 10, 30)
QUALITIES = (10, 20, 30)
PSNR_LIMIT = 1.0
STRESS_COMMIT = "168e5070cacbdeeaefab58ed469dd7e90db4aa3f"
STRESS_DIR = Path("outputs/run-w0-d")
STRESS_SHA = "6ae88428a147467a7dc6d6025966fe7f994632013ecf0f61ffeed04ecad4c238"


def read_csv(path):
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def verify_reference(row, archive, reference, exact_bytes):
    if w0.digest(archive / reference["file"]) != reference["sha256"]:
        raise ValueError(f"Historical file hash mismatch: {reference['file']}")
    same_bytes = row["sha256"] == reference["sha256"]
    if row["extracted_bits"] != reference["extracted_bits"] or row["original_bits"] != reference["original_bits"]:
        raise ValueError(f"d2=20 bit mismatch: {row['file']}")
    for key in ("psnr_marked_db", "psnr_jpeg_vs_original_db"):
        if reference[key] and abs(row[key] - float(reference[key])) > 1e-10:
            raise ValueError(f"d2=20 {key} mismatch: {row['file']}")
    if exact_bytes and not same_bytes:
        raise ValueError(f"d2=20 same-environment byte mismatch: {row['file']}")
    return {"file": row["file"], "reference": (archive / reference["file"]).as_posix(),
            "bits_and_psnr_match": True, "sha256_match": same_bytes}


def evaluate(image_id, original, marked_psnr, pixels, file, d2, quality, decisions):
    row = w0.measure(image_id, original, marked_psnr, pixels, file, quality, d2=d2)
    scores, bits, midpoint, gap, notices = stress.decision_scores(pixels, d2=d2)
    if bits != row["extracted_bits"]:
        raise ValueError(f"Diagnostic labels differ from public bit API: {file}")
    # Ground truth is used only after both decoder calls have finished.
    means = [float(scores[[bit == label for bit in w0.PAYLOAD]].mean()) for label in "01"]
    row.update(subsampling="" if quality is None else "4:4:4",
               source_png="" if quality is None else f"{image_id}_d2_{d2}.png",
               mean_score_true_0=means[0], mean_score_true_1=means[1],
               score_order_reversed=means[0] > means[1], all_bits_flipped=row["error_count"] == 32)
    for index, (score, bit) in enumerate(zip(scores, bits), 1):
        decisions.append({
            "image_id": image_id, "d2": d2, "quality": quality, "position_1based": index,
            "score": score, "cluster_bit": bit, "centroid_midpoint": midpoint,
            "signed_margin_to_midpoint": None if midpoint is None else score - midpoint,
            "cluster_gap": gap, "diagnostic_warnings": json.dumps(notices),
        })
    return row


def pairs(rows):
    reference = {(row["image_id"], row["quality"]): row for row in rows if row["d2"] == 20}
    for row in rows:
        if row["d2"] == 20:
            continue
        base = reference[row["image_id"], row["quality"]]
        delta = row["psnr_marked_db"] - base["psnr_marked_db"]
        yield {
            "image_id": row["image_id"], "d2": row["d2"], "quality": row["quality"],
            "candidate_error_count": row["error_count"], "baseline_error_count": base["error_count"],
            "delta_ber": row["ber"] - base["ber"], "delta_png_psnr_db": delta,
            "similar_png_psnr": abs(delta) <= PSNR_LIMIT,
            "delta_jpeg_psnr_db": None if row["quality"] is None else
            row["psnr_jpeg_vs_original_db"] - base["psnr_jpeg_vs_original_db"],
        }


def plot_results(output):
    rows = read_csv(output / "results.csv")
    data = {(r["image_id"], int(r["d2"]), r["quality"]): r for r in rows}
    images = sorted({r["image_id"] for r in rows})
    d2_values = sorted(SETTINGS)
    colors = ("#9c421d", "#366197", "#36745d")
    fig, axes = plt.subplots(len(images), 3, figsize=(10, 8), layout="constrained")
    for i, image in enumerate(images):
        png, jpeg, ber = axes[i]
        baseline = float(data[image, 20, ""]["psnr_marked_db"])
        png.axhspan(baseline - PSNR_LIMIT, baseline + PSNR_LIMIT, color="#e5ecf5")
        png.plot(d2_values, [float(data[image, d, ""]["psnr_marked_db"]) for d in d2_values],
                 color="#202c43", marker="o")
        for j, (q, color) in enumerate(zip(QUALITIES, colors)):
            jpeg.plot(d2_values, [float(data[image, d, str(q)]["psnr_jpeg_vs_original_db"])
                                  for d in d2_values], marker="o", color=color, label=f"Q{q}")
            ber.bar([d + (j - 1) * 2 for d in d2_values],
                    [100 * float(data[image, d, str(q)]["ber"]) for d in d2_values],
                    width=1.8, color=color)
        png.set_ylabel(image)
        ber.set_ylim(0, 105)
        for ax in axes[i]:
            ax.set_xticks(d2_values)
            ax.grid(axis="y", alpha=0.25)
    for ax, title in zip(axes[0], ("Marked PNG vs original (dB)", "Decoded JPEG vs original (dB)", "Bit error rate (%)")):
        ax.set_title(title)
    for ax in axes[-1]:
        ax.set_xlabel("d2")
    axes[0, 1].legend(loc="best", ncols=3, fontsize=8)
    fig.savefig(output / "comparison.png", dpi=160)
    plt.close(fig)


def run(output):
    provenance = json.loads(distribution("blind_watermark").read_text("direct_url.json"))
    if provenance["vcs_info"]["commit_id"] != w0.UPSTREAM:
        raise ValueError("Unexpected upstream commit")
    w0_path = stress.BASELINE / "manifest.json"
    stress_path = STRESS_DIR / "manifest.json"
    if w0.digest(w0_path) != stress.BASELINE_MANIFEST_SHA or w0.digest(stress_path) != STRESS_SHA:
        raise ValueError("Unexpected historical manifests")
    baseline = json.loads(w0_path.read_text(encoding="utf-8"))
    stress_manifest = json.loads(stress_path.read_text(encoding="utf-8"))
    for archive, manifest in ((stress.BASELINE, baseline), (STRESS_DIR, stress_manifest)):
        if w0.digest(archive / "results.csv") != manifest["files"]["results.csv"]:
            raise ValueError(f"Historical results CSV hash mismatch: {archive}")
    packages = {name: version(name) for name in (*baseline["packages"], "matplotlib")}
    same_environment = (
        platform.platform() == baseline["platform"] == stress_manifest["platform"]
        and platform.python_version() == baseline["python"] == stress_manifest["python"]
        and all(packages[name] == value for name, value in baseline["packages"].items())
        and features.version_feature("libjpeg_turbo") == baseline["pillow_libjpeg_turbo"]
    )
    references = {}
    for archive in (stress.BASELINE, STRESS_DIR):
        for row in read_csv(archive / "results.csv"):
            if (archive == stress.BASELINE and not row["quality"]) or (
                archive == STRESS_DIR and row["quality"] in {"10", "20", "30"}
                and row["subsampling"] == "4:4:4"
            ):
                references[row["image_id"], row["quality"]] = archive, row

    sources = stress.inputs(baseline)
    originals = {image_id: w0.load_rgb(original) for image_id, original, _ in sources}
    output.mkdir(parents=True, exist_ok=False)
    rows, decisions, checks, png_rows = [], [], [], []
    manifest = {
        "status": "error", "command": ["python", "-m", "watermark_baseline.g2", "--output-dir", str(output)],
        "w0_commit": stress.BASELINE_COMMIT, "w0_manifest_sha256": stress.BASELINE_MANIFEST_SHA,
        "w0_d_commit": STRESS_COMMIT, "w0_d_manifest_sha256": STRESS_SHA,
        "upstream": provenance, "python": platform.python_version(), "platform": platform.platform(),
        "packages": packages, "opencv": cv2.__version__, "pillow_jpeg": features.version("jpg"),
        "pillow_libjpeg_turbo": features.version_feature("libjpeg_turbo"),
        **{key: baseline[key] for key in ("inputs", "payload", "keys", "mode", "fast_mode",
                                           "d1", "block_shape", "decoder", "color", "psnr")},
        "d2_values": sorted(SETTINGS), "d2_reference": 20, "png_psnr_max_absolute_delta_db": PSNR_LIMIT,
        "jpeg": {"qualities": QUALITIES, "encoder": "Pillow RGB", **w0.JPEG},
        "historical_byte_match_required": same_environment, "baseline_checks": checks,
        "no_attack_failures": [],
    }
    try:
        (output / "opencv-build.txt").write_text(cv2.getBuildInformation(), encoding="utf-8", newline="\n")
        for d2 in SETTINGS:
            for image_id, original in originals.items():
                marked = output / f"{image_id}_d2_{d2}.png"
                blocks = w0.embed(original, marked, d2=d2)
                if blocks != baseline["blocks_per_channel"][image_id]:
                    raise ValueError(f"Unexpected capacity for {image_id}")
                pixels = w0.load_rgb(marked)
                row = evaluate(image_id, original, w0.psnr(original, pixels), pixels, marked, d2, None, decisions)
                rows.append(row)
                png_rows.append(row)
                if row["error_count"] or json.loads(row["warnings"]):
                    manifest["no_attack_failures"].append(marked.name)
                if d2 == 20:
                    checks.append(verify_reference(row, *references[image_id, ""], same_environment))

        for png in png_rows:
            image_id, d2 = png["image_id"], png["d2"]
            for q in QUALITIES:
                marked = output / png["file"]
                file = output / f"{marked.stem}_q{q}.jpg"
                pixels = stress.encode(marked, file, q, w0.JPEG["subsampling"])
                row = evaluate(image_id, originals[image_id], png["psnr_marked_db"], pixels, file, d2, q, decisions)
                rows.append(row)
                if d2 == 20:
                    checks.append(verify_reference(row, *references[image_id, str(q)], same_environment))
        stress.write_csv(output / "paired.csv", list(pairs(rows)))
        stress.write_csv(output / "results.csv", rows)
        plot_results(output)
        manifest["status"] = "complete"
    except Exception as error:
        manifest["error"] = repr(error)
        raise
    finally:
        if rows:
            stress.write_csv(output / "results.csv", rows)
        if decisions:
            stress.write_csv(output / "decision_scores.csv", decisions)
        manifest["files"] = {path.name: w0.digest(path) for path in sorted(output.iterdir())}
        (output / "manifest.json").write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n"
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True, type=Path)
    run(parser.parse_args().output_dir)
