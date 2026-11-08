"""Audit the saved mechanism counts against the per-block observations."""
from collections import Counter
import csv
import gzip
import json
from pathlib import Path

import numpy as np

from watermark_baseline import __main__ as w0
from watermark_baseline.mechanism import circular_delta, hard_votes

OUT = Path("outputs/run-g5-diagnostics")


def test_modulus_boundary_and_circular_wrap():
    np.testing.assert_array_equal(hard_votes(np.array([[18, 10], [19, 11], [36, 20]])),
                                  [[False, False], [True, True], [False, False]])
    np.testing.assert_allclose(circular_delta(np.array([0.9, 0.1]), np.array([0.1, 0.9])),
                               [0.2, -0.2])


def test_archive_counts_match_block_rows():
    manifest = json.loads((OUT / "manifest.json").read_text(encoding="utf-8"))
    for file, sha in manifest["files"].items():
        assert w0.digest(OUT / file) == sha
    for file, sha in manifest["archived_images"].items():
        assert w0.digest(Path(file)) == sha
    counts, flips, png = Counter(), Counter(), {}
    with gzip.open(OUT / "blocks.csv.gz", "rt", newline="", encoding="utf-8") as stream:
        for row in csv.DictReader(stream):
            image, channel, stage = (row[key] for key in ("image", "channel", "stage"))
            key = image, channel, row["block_y"], row["block_x"]
            a, b, c, d = (float(row[f"s{i}"]) for i in range(4))
            if stage == "quantized_index_order":
                counts[image, channel, "all"] += 1
                counts[image, channel, "top_swap"] += b > a
                counts[image, channel, "lower_swap"] += b < c
            else:
                assert a >= b >= c >= d >= 0
            vote = row["vote0"], row["vote1"]
            if stage == "PNG":
                png[key] = vote
            if stage.startswith("Q"):
                for j in range(2):
                    flips[image, channel, stage[1:], str(j)] += vote[j] != png[key][j]
    with (OUT / "ordering.csv").open(newline="", encoding="utf-8") as stream:
        for row in csv.DictReader(stream):
            key = row["image"], row["channel"], row["event"]
            if row["event"] != "neither":
                assert int(row["blocks"]) == counts[key]
    with (OUT / "jpeg_shifts.csv").open(newline="", encoding="utf-8") as stream:
        for row in csv.DictReader(stream):
            if row["group"] == "all":
                key = tuple(row[f] for f in ("image", "channel", "quality", "singular_index"))
                assert int(row["flips"]) == flips[key]
