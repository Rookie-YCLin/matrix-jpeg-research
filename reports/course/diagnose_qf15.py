"""Trace pinned K-means through the unchanged public bit decoder for two archived QF15 cases."""
import argparse
import csv
from importlib.metadata import distribution
import json
from pathlib import Path
import sys

from blind_watermark.bwm_core import one_dim_kmeans
import numpy as np

from experiments.svd_qim_sweep import configured_instance, extract_with_qim
from experiments import ori_qf_scan as fixed

ROOT = Path(__file__).resolve().parents[2]
ARCHIVE = ROOT / "outputs/svd-qim-qf15-selected/results.csv"


def inspect(paired):
    upstream = json.loads(distribution("blind_watermark").read_text("direct_url.json"))
    assert upstream["vcs_info"]["commit_id"] == fixed.UPSTREAM_COMMIT
    with ARCHIVE.open(encoding="utf-8", newline="") as stream:
        rows = [r for r in csv.DictReader(stream) if r["payload"] == "primary" and r["qf"] == "15"]
    result = {}
    for row in rows:
        variant = row["variant"]
        path = paired / f"{variant}_qf15.jpg"
        assert fixed.sha256_file(path) == row["attack_sha256"]
        observed = {}

        def trace(frame, event, _):
            if frame.f_code is not one_dim_kmeans.__code__:
                return None
            if event == "return":
                local = frame.f_locals
                observed.update(scores=local["inputs"].tolist(),
                                centers=[float(c) for c in local["center"]],
                                threshold=float(local["threshold"]))
            return trace

        previous = sys.gettrace()
        sys.settrace(trace)
        try:
            bits = extract_with_qim(fixed.read_rgb(path), 36 if variant == "upstream" else 90, 20)
        finally:
            sys.settrace(previous)
        expected = row["expected_bits"]
        assert bits == row["extracted_bits"]
        wm = configured_instance(36 if variant == "upstream" else 90, 20)
        wm.wm_size = fixed.WM_SIZE
        scores = wm.extract_decrypt(np.asarray(observed["scores"]))
        observed["scores_payload_order"] = scores.tolist()
        assert scores.shape == (32,)
        assert "".join(str(int(v)) for v in scores > observed["threshold"]) == bits
        observed["truth_group_ranges"] = {
            label: [float(v.min()), float(v.max())]
            for label in "01" if (v := scores[np.array(list(expected)) == label]).size
        }
        result[variant] = dict(observed, expected_bits=expected, extracted_bits=bits,
                               attack_sha256=row["attack_sha256"])
    return {"upstream_commit": fixed.UPSTREAM_COMMIT, "qf": 15, "variants": result}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--paired", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = inspect(args.paired)
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(report, stream, indent=2)
        stream.write("\n")
