"""Compare two independently generated R1 archives in the same environment."""
import argparse
import csv
from hashlib import sha256
import json
from pathlib import Path

import numpy as np

from analysis.r1 import ATOL, JPEG_SHA256, RTOL, SHAPE, validate_energies


def load_run(path):
    manifest = json.loads((path / "manifest.json").read_text(encoding="utf-8"))
    if manifest["status"] != "passed":
        raise ValueError(f"{path}: run did not pass")
    weights = np.load(path / "weights.npy", allow_pickle=False)
    if weights.dtype != np.float64:
        raise ValueError(f"{path}: W must be float64")
    validate_energies(weights, SHAPE[0])
    with (path / "sensitivity.csv").open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    keys = [(int(r["i"]), int(r["Q"])) for r in rows]
    if keys != [(i, q) for i in range(1, SHAPE[0] + 1) for q in JPEG_SHA256]:
        raise ValueError(f"{path}: wrong CSV direction/quality indices")
    return manifest, weights, {column: np.array([float(r[column]) for r in rows])
                               for column in ("sigma_i", "S_i")}


def compare(first, second):
    if first.resolve() == second.resolve():
        raise ValueError("Replay must come from a different output directory")
    a, wa, ca = load_run(first)
    b, wb, cb = load_run(second)
    for key in ("environment", "input", "jpeg_sources", "settings", "tolerances"):
        if a[key] != b[key]:
            raise ValueError(f"Replay metadata differs: {key}")
    gaps = {}
    for label, left, right in (("W", wa, wb), ("sigma_i", ca["sigma_i"], cb["sigma_i"]),
                               ("S_i", ca["S_i"], cb["S_i"])):
        np.testing.assert_allclose(left, right, rtol=RTOL, atol=ATOL, equal_nan=False)
        gaps[label] = float(np.max(np.abs(left - right)))
    hashes = {}
    for name in ("weights.npy", "sensitivity.csv"):
        left, right = (sha256((path / name).read_bytes()).hexdigest() for path in (first, second))
        hashes[name] = {"first": left, "second": right, "byte_identical": left == right}
    return {
        "status": "passed", "first": first.as_posix(), "second": second.as_posix(),
        "rtol": RTOL, "atol": ATOL, "max_absolute_differences": gaps, "sha256": hashes,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("first", type=Path)
    parser.add_argument("second", type=Path)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    try:
        report = compare(args.first, args.second)
        with args.report.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(json.dumps(report, indent=2) + "\n")
    except (ValueError, AssertionError, OSError) as error:
        parser.exit(1, f"R1 replay failed: {error}\n")
    print(f"R1 replay PASS: {args.report}")


if __name__ == "__main__":
    main()
