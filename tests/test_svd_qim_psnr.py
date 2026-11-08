"""Numerical checks independent of optional watermark dependencies."""
import csv
from hashlib import sha256
import json
from math import log10
from pathlib import Path

import numpy as np
import pytest

from experiments.svd_qim_psnr import rgb_psnr


def test_rgb_peak_and_uint8_overflow():
    black = np.zeros((2, 2, 3), dtype=np.uint8)
    white = np.full_like(black, 255)
    assert rgb_psnr(black, white) == rgb_psnr(white, black) == (65025, 0)
    assert rgb_psnr(black, black) == (0, float("inf"))


def test_mse_averages_all_channels():
    a = np.zeros((1, 2, 3), dtype=np.uint8)
    b = a.copy()
    b[0, 0, 2] = 30
    assert rgb_psnr(a, b) == pytest.approx((150, 26.369891018122292))


@pytest.mark.parametrize("shape", [(1, 2, 4), (1, 3, 3), (1, 2), (0, 2, 3)])
def test_rejects_bad_shape(shape):
    with pytest.raises(ValueError):
        rgb_psnr(np.zeros((1, 2, 3), dtype=np.uint8), np.zeros(shape, dtype=np.uint8))


def test_rejects_non_uint8():
    with pytest.raises(ValueError):
        rgb_psnr(np.zeros((1, 2, 3), dtype=np.uint8), np.zeros((1, 2, 3)))


def test_paired_archive_agrees_with_manifest_and_psnr_formula():
    folder = Path(__file__).resolve().parents[1] / "outputs/svd-qim-psnr-qf15"
    path = folder / "results.csv"
    manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
    assert sha256(path.read_bytes()).hexdigest() == manifest["files_sha256"]["results.csv"]
    with path.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    table = {(r["variant"], r["stage"]): r for r in rows}
    assert len(rows) == len(table) == 4
    for stage in ("uncompressed_embedded", "qf15_attacked"):
        original, g6 = (table[variant, stage] for variant in ("upstream", "svd_step_90"))
        delta = float(g6["psnr_db"]) - float(original["psnr_db"])
        for row in (original, g6):
            assert float(row["psnr_db"]) == pytest.approx(10 * log10(65025 / float(row["mse_rgb_8bit"])))
            assert float(row["delta_g6_minus_upstream_db"]) == pytest.approx(delta)
            assert row["sha256"] == manifest["files_sha256"][row["file"]]
            bits = row["extracted_bits"]
            assert len(bits) == 32 and set(bits) <= {"0", "1"}
            errors = sum(a != b for a, b in zip(bits, manifest["payload"]))
            assert int(row["errors"]) == errors
            assert float(row["ber"]) == errors / 32
            assert row["archived_bits_match"] == "True"
    assert table["upstream", "qf15_attacked"]["errors"] == "32"
    assert table["svd_step_90", "qf15_attacked"]["errors"] == "0"
