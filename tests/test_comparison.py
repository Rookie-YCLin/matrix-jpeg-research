import json
from pathlib import Path

import numpy as np
from PIL import Image
import pytest

import charts
import experiment
import svd

ROOT = Path(__file__).resolve().parents[1]
QUALITIES = (40, 60, 80, 95)


def test_signed_projection_matches_frobenius_inner_product():
    original = np.array([[0., 4., 0.], [3., 0., 0.]])
    factors = svd.decompose(original)
    u, sigma, vh = factors
    np.testing.assert_allclose(svd.project_onto_rank_one_directions(original, factors), sigma)
    decoded = np.array([[1., -8., 2.], [6., 3., 9.]])
    expected = [np.sum(decoded * np.outer(u[:, i], vh[i])) for i in range(len(sigma))]
    actual = svd.project_onto_rank_one_directions(decoded, factors)
    np.testing.assert_allclose(actual, expected)
    assert actual[0] < 0


@pytest.fixture(scope="module")
def comparison(tmp_path_factory):
    output = tmp_path_factory.mktemp("comparison") / "run"
    experiment.run(ROOT / "data/ascent.png", output, QUALITIES)
    return output


def test_comparison_recomputes_measurements_from_each_jpeg(comparison):
    with Image.open(ROOT / "data/ascent.png") as image:
        original = np.array(image, dtype=np.float64)
    u, sigma, vh = svd.decompose(original)
    metrics = charts.read_rows(comparison / "jpeg_metrics.csv")
    projections = charts.read_rows(comparison / "projections.csv")
    spectra = charts.read_rows(comparison / "spectrum.csv")
    manifest = json.loads((comparison / "manifest.json").read_text())
    assert manifest["jpeg_settings"]["qualities"] == list(QUALITIES)
    assert [int(row["quality_factor"]) for row in metrics] == list(QUALITIES)
    for q, row in zip(QUALITIES, metrics, strict=True):
        jpeg = comparison / f"jpeg_q{q}.jpg"
        with Image.open(jpeg) as image:
            assert image.format == "JPEG"
            decoded = np.array(image, dtype=np.float64)
        with Image.open(comparison / f"jpeg_q{q}_decoded.png") as image:
            np.testing.assert_array_equal(np.array(image), decoded)
        mse = np.mean((original - decoded)**2)
        assert float(row["mse"]) == pytest.approx(mse)
        assert float(row["psnr_db"]) == pytest.approx(10 * np.log10(255**2 / mse))
        assert int(row["jpeg_bytes"]) == jpeg.stat().st_size
        selected = [item for item in projections if int(item["quality_factor"]) == q]
        assert [int(item["i"]) for item in selected] == list(range(1, 513))
        expected = np.diag(u.T @ decoded @ vh.T)
        np.testing.assert_allclose([float(item["coefficient"]) for item in selected], expected,
                                   rtol=1e-8, atol=1e-10)
        np.testing.assert_allclose([float(item["original_sigma"]) for item in selected], sigma)
        np.testing.assert_allclose([float(item["delta"]) for item in selected], expected - sigma,
                                   rtol=1e-8, atol=1e-10)
        selected = [item for item in spectra if item["image"] == f"jpeg_q{q}"]
        np.testing.assert_allclose([float(item["sigma"]) for item in selected],
                                   np.linalg.svd(decoded, compute_uv=False), rtol=1e-8, atol=1e-10)

    baseline = ROOT / "outputs/run-001"
    assert (comparison / "jpeg_q80.jpg").read_bytes() == (baseline / "jpeg_q80.jpg").read_bytes()
    assert metrics[2] == charts.read_rows(baseline / "jpeg_metrics.csv")[0]


def test_comparison_plots_use_csv_columns(comparison):
    rows = charts.read_rows(comparison / "projections.csv")
    figure = charts.projection_figure(rows)
    coefficients, delta = figure.axes
    for q, c_line, d_line in zip(QUALITIES, coefficients.lines[1:], delta.lines, strict=True):
        group = [row for row in rows if int(row["quality_factor"]) == q]
        np.testing.assert_array_equal(c_line.get_xdata(), [int(row["i"]) for row in group])
        np.testing.assert_array_equal(c_line.get_ydata(), [float(row["coefficient"]) for row in group])
        np.testing.assert_array_equal(d_line.get_ydata(), [float(row["delta"]) for row in group])
    charts.plt.close(figure)
    rows = charts.read_rows(comparison / "jpeg_metrics.csv")
    figure = charts.quality_figure(rows)
    axis, = figure.axes
    for row, line, label in zip(rows, axis.lines, axis.texts, strict=True):
        assert line.get_xdata().tolist() == [int(row["jpeg_bytes"])]
        assert line.get_ydata().tolist() == [float(row["psnr_db"])]
        assert label.get_text() == f'Q={row["quality_factor"]}'
    charts.plt.close(figure)
    for name in ("projections.png", "jpeg_metrics.png", "rank_errors.png", "spectra.png"):
        with Image.open(comparison / name) as image:
            image.verify()
