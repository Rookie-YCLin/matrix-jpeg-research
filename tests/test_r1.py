"""R1 mathematical, JPEG-layout and artifact regression checks."""
import csv
from io import BytesIO
import json
from pathlib import Path

import numpy as np
from PIL import Image
import pytest
from scipy.fft import dct, dctn, idct

from analysis.compare_r1 import compare
from analysis.jpeg_tables import verified_table
from analysis.r1 import (ATOL, JPEG_SHA256, PNG_SHA256, RTOL, SHAPE, block_dct,
                         energy_matrices, read_fixed, run, sensitivity, validate_energies)

ROOT = Path(__file__).resolve().parents[1]
JPEG_DIR = ROOT / "outputs/run-m2"


def test_orthonormal_dct_matrix():
    transform = dct(np.eye(8), type=2, norm="ortho", axis=0)
    np.testing.assert_allclose(transform @ transform.T, np.eye(8), rtol=0, atol=ATOL)


def test_dct_inverse_and_parseval():
    samples = np.array([[0., 1., -4., 2., 8., 3., 5., -6.]])
    coefficients = block_dct(samples)
    assert coefficients.dtype == np.float64
    np.testing.assert_allclose(idct(coefficients, type=2, norm="ortho").reshape(samples.shape),
                               samples, rtol=0, atol=ATOL)
    np.testing.assert_allclose(np.sum(coefficients**2), np.sum(samples**2), rtol=0, atol=ATOL)


def test_rank_one_blocks_agree_with_direct_2d_dct():
    u = np.arange(1., 17.)
    v = np.sin(np.arange(24.))
    u /= np.linalg.norm(u)
    v /= np.linalg.norm(v)
    direct_energy = np.zeros((8, 8))
    a, b = block_dct(u[None, :])[0], block_dct(v[None, :])[0]
    for p, block_u in enumerate(u.reshape(-1, 8)):
        for q, block_v in enumerate(v.reshape(-1, 8)):
            direct = dctn(np.outer(block_u, block_v), type=2, norm="ortho")
            np.testing.assert_allclose(direct, np.outer(a[p], b[q]), rtol=0, atol=ATOL)
            direct_energy += direct**2
    weights = energy_matrices(u[None, :], v[None, :])
    assert validate_energies(weights, 1) <= ATOL
    np.testing.assert_allclose(weights[0], direct_energy, rtol=0, atol=ATOL)


@pytest.mark.parametrize("bad", [np.zeros((1, 7, 8)), -np.ones((1, 8, 8)), np.zeros((1, 8, 8))])
def test_invalid_weight_shape_sign_or_total_rejected(bad):
    with pytest.raises((ValueError, AssertionError)):
        validate_energies(bad, 1)


def test_sensitivity_hand_calculation():
    weights = np.zeros((8, 8))
    weights[1, 2], weights[2, 1] = .25, .75
    steps = np.ones((8, 8), dtype=int)
    steps[1, 2], steps[2, 1] = 2, 4
    assert sensitivity(weights, steps) == pytest.approx(np.sqrt(13), rel=0, abs=ATOL)


def test_asymmetric_dqt_distinguishes_zigzag_and_transpose():
    # Inverse scan indices from T.81 Annex A, one-based for byte values 1..64.
    expected = np.array([
        [1, 2, 6, 7, 15, 16, 28, 29],
        [3, 5, 8, 14, 17, 27, 30, 43],
        [4, 9, 13, 18, 26, 31, 42, 44],
        [10, 12, 19, 25, 32, 41, 45, 54],
        [11, 20, 24, 33, 40, 46, 53, 55],
        [21, 23, 34, 39, 47, 52, 56, 61],
        [22, 35, 38, 48, 51, 57, 60, 62],
        [36, 37, 49, 50, 58, 59, 63, 64],
    ])
    buffer = BytesIO()
    Image.new("L", (16, 8), 128).save(buffer, "JPEG", qtables=[expected.ravel().tolist()])
    table, evidence = verified_table(buffer.getvalue(), (8, 16))
    assert evidence["raw_dqt_zigzag"] == list(range(1, 65))
    np.testing.assert_array_equal(table, expected)


@pytest.mark.parametrize("q", list(JPEG_SHA256))
def test_archived_m2_jpeg_table(q):
    payload = read_fixed(JPEG_DIR / f"jpeg_q{q}.jpg", JPEG_SHA256[q])
    table, evidence = verified_table(payload, SHAPE)
    assert evidence["component_id"] == 1 and evidence["table_id"] == 0
    assert evidence["precision_bits"] == 8 and table.shape == (8, 8)
    assert np.all(table > 0)


def test_wrong_input_rejected_before_output(tmp_path):
    png = tmp_path / "ascent.png"
    png.write_bytes((ROOT / "data/ascent.png").read_bytes() + b"x")
    output = tmp_path / "run"
    with pytest.raises(ValueError, match="SHA-256"):
        run(png, JPEG_DIR, output)
    assert not output.exists()


def test_full_r1_csv_weights_and_replay(tmp_path):
    image = ROOT / "data/ascent.png"
    first, replay = tmp_path / "run", tmp_path / "replay"
    run(image, JPEG_DIR, first)
    run(image, JPEG_DIR, replay)
    evidence = compare(first, replay)
    assert evidence["status"] == "passed"
    with pytest.raises(ValueError, match="different output directory"):
        compare(first, first)
    with pytest.raises(FileExistsError):
        run(image, JPEG_DIR, first)
    manifest = json.loads((first / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["input"]["sha256"] == PNG_SHA256
    assert manifest["validation"]["directions_checked"] == 512
    weights = np.load(first / "weights.npy", allow_pickle=False)
    with (first / "sensitivity.csv").open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == 2048
    with (JPEG_DIR / "spectrum.csv").open(newline="", encoding="utf-8") as stream:
        sigma = [float(row["sigma"]) for row in csv.DictReader(stream) if row["image"] == "original"]
    for q in JPEG_SHA256:
        selected = [row for row in rows if int(row["Q"]) == q]
        steps = np.array(manifest["jpeg_sources"][str(q)]["natural_order"], dtype=np.float64)
        np.testing.assert_allclose([float(row["S_i"])**2 for row in selected],
                                   weights.reshape(512, 64) @ (steps.ravel()**2),
                                   rtol=RTOL, atol=ATOL)
        np.testing.assert_allclose([float(row["sigma_i"]) for row in selected],
                                   sigma, rtol=RTOL, atol=ATOL)
