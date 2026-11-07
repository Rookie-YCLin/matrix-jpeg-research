import csv
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
from PIL import Image
import pytest

ROOT = Path(__file__).resolve().parents[1]
RANKS = [1, 5, 10, 20, 50, 100]


def read_csv(path):
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


@pytest.fixture(scope="module")
def experiment_output(tmp_path_factory):
    output = tmp_path_factory.mktemp("experiment") / "run"
    result = subprocess.run(
        [sys.executable, "-m", "experiment", "--input", "data/ascent.png",
         "--output-dir", str(output)],
        cwd=ROOT, capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    return output


def test_output_manifest_and_images(experiment_output):
    output = experiment_output
    manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["status"] == "passed"
    assert manifest["input"]["sha256"] == sha256((ROOT / "data/ascent.png").read_bytes()).hexdigest()
    assert manifest["input"]["shape"] == [512, 512]
    assert manifest["jpeg_settings"] == {"quality": 80, "optimize": False, "progressive": False}
    assert manifest["jpeg_library"]
    assert set(manifest["artifacts"]) == {p.name for p in output.iterdir()} - {"manifest.json"}

    for k in RANKS:
        with Image.open(output / f"rank_{k:03}.png") as image:
            assert (image.format, image.mode, image.size) == ("PNG", "L", (512, 512))
            image.load()
    for filename in ("reconstructions.png", "rank_errors.png", "spectra.png"):
        with Image.open(output / filename) as image:
            image.verify()


def test_jpeg_metrics_and_spectra_use_decoded_pixels(experiment_output):
    output = experiment_output
    with Image.open(ROOT / "data/ascent.png") as image:
        original = np.array(image, dtype=np.float64)
    jpeg = output / "jpeg_q80.jpg"
    with Image.open(jpeg) as image:
        assert image.format == "JPEG" and image.mode == "L"
        decoded = np.array(image, dtype=np.float64)
    with Image.open(output / "jpeg_decoded.png") as image:
        np.testing.assert_array_equal(np.array(image), decoded)

    metrics, = read_csv(output / "jpeg_metrics.csv")
    assert int(metrics["quality_factor"]) == 80
    assert int(metrics["jpeg_bytes"]) == jpeg.stat().st_size
    mse = np.mean((original - decoded)**2)
    assert mse > 0
    assert float(metrics["mse"]) == pytest.approx(mse)
    assert float(metrics["psnr_db"]) == pytest.approx(10 * np.log10(255**2 / mse))

    spectra = read_csv(output / "spectrum.csv")
    errors = read_csv(output / "rank_errors.csv")
    for name, matrix in (("original", original), ("jpeg_q80", decoded)):
        spectrum = [row for row in spectra if row["image"] == name]
        assert [int(row["i"]) for row in spectrum] == list(range(1, 513))
        expected = np.linalg.svd(matrix, compute_uv=False)
        np.testing.assert_allclose([float(row["sigma"]) for row in spectrum],
                                   expected, rtol=1e-8, atol=1e-10)
        np.testing.assert_allclose([float(row["cumulative_energy"]) for row in spectrum],
                                   np.cumsum(expected**2) / np.sum(expected**2),
                                   rtol=1e-8, atol=1e-12)
        rows = [row for row in errors if row["image"] == name]
        assert [int(row["k"]) for row in rows] == [0, *RANKS, 512]
        residual = np.array([float(row["relative_squared"]) for row in rows])
        tail = np.array([float(row["relative_tail_squared"]) for row in rows])
        np.testing.assert_allclose(residual, tail, rtol=1e-8, atol=1e-12)
        assert np.all(np.diff(residual) <= 1e-12)
        assert residual[-1] <= 1e-12
