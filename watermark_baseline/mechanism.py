"""Observe the original embedder and archived JPEG decoder without changing either."""
import argparse
import csv
import gzip
from importlib.metadata import distribution, version
import io
import json
from pathlib import Path
import platform
from unittest.mock import patch

import cv2
import numpy as np
from PIL import features
from blind_watermark import bwm_core as upstream

from . import __main__ as w0
from . import stress

JPEG_DIR = Path("outputs/run-w0-d")
JPEG_MANIFEST = "6ae88428a147467a7dc6d6025966fe7f994632013ecf0f61ffeed04ecad4c238"
STEPS = np.array([36.0, 20.0], dtype=np.float32)
CHANNELS = ("Y", "U", "V")


def spectrum(block, shuffle, shape):
    return upstream.svd(upstream.dct(block).flatten()[shuffle].reshape(shape))[1]


def observe_embedding(rgb, factory=w0.new_watermark):
    wm = factory()
    core = wm.bwm_core
    wm.read_img(img=w0.to_bgr(rgb))
    wm.read_wm([int(bit) for bit in w0.PAYLOAD], mode="bit")
    records = []
    original_block = core.block_add_wm_slow
    original_svd = upstream.svd

    def observe(arg):
        def capture(matrix):
            u, s, vh = original_svd(matrix)
            captured.append((s.copy(), s))
            return u, s, vh

        captured = []
        with patch.object(upstream, "svd", capture):
            output = original_block(arg)
        (before, after), = captured
        _, shuffle, index = arg
        records.append((before, after.copy(), spectrum(output, shuffle, core.block_shape),
                        int(core.wm_bit[index % w0.BIT_COUNT])))
        return output

    core.block_add_wm_slow = observe
    embedded = wm.embed()
    n = core.block_num
    s, quantized, reconstructed = [np.array([r[j] for r in records]).reshape(3, n, 4) for j in range(3)]
    bits = np.array([r[3] for r in records]).reshape(3, n)
    return embedded, s, quantized, reconstructed, bits, core.ca_block_shape[1]


def extract_spectra(bgr):
    core = w0.new_watermark().bwm_core
    captured = []
    original_svd = upstream.svd

    def capture(matrix):
        u, s, vh = original_svd(matrix)
        captured.append(s.copy())
        return u, s, vh

    core.wm_size = w0.BIT_COUNT
    with patch.object(upstream, "svd", capture):
        actual = core.extract_raw(img=bgr)
    s = np.array(captured).reshape(*actual.shape, 4)
    votes = hard_votes(s)
    np.testing.assert_array_equal((3 * votes[..., 0].astype(int) + votes[..., 1]) / 4, actual)
    return s


def hard_votes(s):
    return (s[..., :2] % STEPS) > STEPS / 2


def circular_delta(start, end):
    return (end - start + 0.5) % 1 - 0.5


def change_rows(image, q, png, jpeg, positions):
    phase = (png[..., :2] % STEPS) / STEPS
    attacked = (jpeg[..., :2] % STEPS) / STEPS
    circular = circular_delta(phase, attacked)
    delta = (jpeg[..., :2] - png[..., :2]) / STEPS
    flipped = hard_votes(png) != hard_votes(jpeg)
    for c, channel in enumerate(CHANNELS):
        for j in range(2):
            for by, values in (("all", ("all",)), ("position", range(1, 33)), ("png_phase_bin", range(8))):
                for value in values:
                    selector = np.ones(phase.shape[1], dtype=bool)
                    if by == "position":
                        selector = positions == value
                    elif by == "png_phase_bin":
                        selector = np.floor(phase[c, :, j] * 8) == value
                    shifts = delta[c, selector, j]
                    wrapped = circular[c, selector, j]
                    n = shifts.size
                    errors = int(flipped[c, selector, j].sum())
                    yield {
                        "image": image, "quality": q, "channel": channel, "singular_index": j,
                        "group": by, "value": value, "blocks": n, "flips": errors,
                        "flip_rate": errors / n if n else None,
                        "positive_delta": int(np.count_nonzero(shifts > 0)),
                        "negative_delta": int(np.count_nonzero(shifts < 0)),
                        "mean_delta_over_d": float(shifts.mean()) if n else None,
                        "positive_circular": int(np.count_nonzero(wrapped > 0)),
                        "negative_circular": int(np.count_nonzero(wrapped < 0)),
                        "mean_circular": float(wrapped.mean()) if n else None,
                    }


def read_manifest(directory, sha):
    path = directory / "manifest.json"
    if w0.digest(path) != sha:
        raise ValueError(f"Historical manifest changed: {path}")
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if w0.digest(directory / "results.csv") != manifest["files"]["results.csv"]:
        raise ValueError(f"Historical results changed: {directory / 'results.csv'}")
    return manifest


def analyze(output):
    upstream_info = json.loads(distribution("blind_watermark").read_text("direct_url.json"))
    if upstream_info["vcs_info"]["commit_id"] != w0.UPSTREAM:
        raise ValueError("Unexpected upstream commit")
    base = read_manifest(stress.BASELINE, stress.BASELINE_MANIFEST_SHA)
    attack = read_manifest(JPEG_DIR, JPEG_MANIFEST)
    sources = stress.inputs(base)
    reference = {}
    for folder in (stress.BASELINE, JPEG_DIR):
        with (folder / "results.csv").open(newline="", encoding="utf-8") as stream:
            for row in csv.DictReader(stream):
                if (folder == stress.BASELINE and not row["quality"]) or (
                    folder == JPEG_DIR and row["quality"] in ("10", "20", "30") and row["subsampling"] == "4:4:4"
                ):
                    reference[row["image_id"], row["quality"]] = row
    output.mkdir(parents=True, exist_ok=False)
    ranks, changes, aggregation, verified, roundtrip = [], [], [], {}, {}
    permutation = np.arange(w0.BIT_COUNT)
    np.random.RandomState(w0.KEYS["password_wm"]).shuffle(permutation)
    payload = np.array([int(bit) for bit in w0.PAYLOAD])

    with (output / "blocks.csv.gz").open("wb") as compressed:
        with gzip.GzipFile(filename="", mode="wb", fileobj=compressed, mtime=0) as zipped:
            with io.TextIOWrapper(zipped, encoding="utf-8", newline="") as stream:
                writer = csv.writer(stream, lineterminator="\n")
                writer.writerow(["image", "channel", "block_y", "block_x", "payload_position", "bit",
                                 "stage", "s0", "s1", "s2", "s3", "remainder0", "remainder1", "vote0", "vote1"])
                for image, original, marked in sources:
                    embedded, source, quantized, immediate, bits, width = observe_embedding(w0.load_rgb(original))
                    png = w0.load_rgb(marked)
                    ok, encoded = cv2.imencode(".png", embedded)
                    if not ok:
                        raise ValueError("Could not reproduce original PNG conversion")
                    np.testing.assert_array_equal(cv2.imdecode(encoded, cv2.IMREAD_COLOR), w0.to_bgr(png))
                    n = source.shape[1]
                    positions = permutation[np.arange(n) % w0.BIT_COUNT]
                    np.testing.assert_array_equal(bits, np.broadcast_to(payload[positions], bits.shape))
                    expected = np.sort(quantized, axis=-1)[..., ::-1]
                    error = np.abs(immediate - expected)
                    scale = np.maximum(expected[..., :1], 1)
                    relative = error / scale
                    if np.max(relative) > 16 * np.finfo(np.float32).eps:
                        raise ValueError(f"Unexpected float32 block round-trip error: {image}")
                    roundtrip[image] = {"max_absolute_error": float(error.max()),
                                        "max_error_over_largest": float(relative.max())}
                    png_s = extract_spectra(w0.to_bgr(png))
                    stages = {"original": source, "quantized_index_order": quantized,
                              "reconstructed_sorted": immediate, "PNG": png_s}
                    verified[marked.as_posix()] = w0.digest(marked)
                    for q in (10, 20, 30):
                        row = reference[image, str(q)]
                        path = JPEG_DIR / row["file"]
                        if w0.digest(path) != attack["files"][path.name] or row["sha256"] != attack["files"][path.name]:
                            raise ValueError(f"Historical JPEG hash mismatch: {path}")
                        verified[path.as_posix()] = row["sha256"]
                        stages[f"Q{q}"] = extract_spectra(w0.to_bgr(w0.load_rgb(path)))
                        changes.extend(change_rows(image, q, png_s, stages[f"Q{q}"], positions + 1))
                    for c, channel in enumerate(CHANNELS):
                        s, t = source[c], quantized[c]
                        delta = t - s
                        top_swap, lower_swap = t[:, 1] > t[:, 0], t[:, 1] < s[:, 2]
                        for event, mask in (("all", np.ones(n, dtype=bool)), ("top_swap", top_swap),
                                            ("lower_swap", lower_swap), ("neither", ~(top_swap | lower_swap))):
                            ranks.append({
                                "image": image, "channel": channel, "event": event, "blocks": int(mask.sum()),
                                "mean_original_gap01": float((s[mask, 0] - s[mask, 1]).mean()) if mask.any() else None,
                                "mean_original_gap12": float((s[mask, 1] - s[mask, 2]).mean()) if mask.any() else None,
                                "mean_delta0": float(delta[mask, 0].mean()) if mask.any() else None,
                                "mean_delta1": float(delta[mask, 1].mean()) if mask.any() else None,
                            })
                    for stage, s in stages.items():
                        votes = hard_votes(s)
                        remainder = s[..., :2] % STEPS
                        if stage != "quantized_index_order" and np.any(np.diff(s, axis=-1) > 0):
                            raise ValueError(f"Unexpected unordered SVD output: {stage}")
                        if stage in ("reconstructed_sorted", "PNG", "Q10", "Q20", "Q30"):
                            core = w0.new_watermark().bwm_core
                            core.wm_size = w0.BIT_COUNT
                            raw = core.extract_avg((3 * votes[..., 0].astype(int) + votes[..., 1]) / 4)
                            scores = np.empty_like(raw)
                            scores[permutation] = raw
                            if stage != "reconstructed_sorted":
                                row = reference[image, "" if stage == "PNG" else stage[1:]]
                                labels = upstream.one_dim_kmeans(raw)
                                ordered = np.empty_like(labels)
                                ordered[permutation] = labels
                                if "".join(str(int(b)) for b in ordered) != row["extracted_bits"]:
                                    raise ValueError(f"Historical bit mismatch: {image} {stage}")
                            for i, score in enumerate(scores):
                                aggregation.append({"image": image, "stage": stage, "position": i + 1,
                                                    "original_bit": payload[i], "score": score})
                        for c, channel in enumerate(CHANNELS):
                            writer.writerows(
                                (image, channel, i // width, i % width, positions[i] + 1, bits[c, i], stage,
                                 *s[c, i], *remainder[c, i], *votes[c, i].astype(int))
                                for i in range(n)
                            )

    for name, data in (("ordering", ranks), ("jpeg_shifts", changes), ("aggregation", aggregation)):
        stress.write_csv(output / f"{name}.csv", data)
    manifest = {
        "status": "complete", "command": ["python", "-m", "watermark_baseline.mechanism", "--output-dir", str(output)],
        "upstream": upstream_info, "python": platform.python_version(), "platform": platform.platform(),
        "packages": {name: version(name) for name in base["packages"]},
        "opencv": cv2.__version__, "pillow_jpeg": features.version("jpg"),
        "pillow_libjpeg_turbo": features.version_feature("libjpeg_turbo"),
        "reference_manifests": {stress.BASELINE.as_posix(): stress.BASELINE_MANIFEST_SHA,
                                JPEG_DIR.as_posix(): JPEG_MANIFEST},
        "archived_images": verified, "original_images": base["inputs"],
        "bit_positions": "1-based payload order after undoing the upstream permutation",
        "float32_block_roundtrip": roundtrip,
        "d1": 36, "d2": 20, "keys": w0.KEYS, "payload": w0.PAYLOAD,
        "files": {path.name: w0.digest(path) for path in sorted(output.iterdir())},
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n",
                                           encoding="utf-8", newline="\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    analyze(parser.parse_args().output_dir)
