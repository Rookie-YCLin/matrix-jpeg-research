"""W0-D acceptance checks for the fixed attack grid and saved evidence."""
import csv
import json
from pathlib import Path

from PIL import Image, JpegImagePlugin
import pytest

from watermark_baseline import __main__ as w0
from watermark_baseline import stress
from watermark_baseline.compare_runs import compare

FIRST = Path("outputs/run-w0-d")
SECOND = Path("outputs/run-w0-d-repeat")
GRID = {(10, 0), (20, 0), (30, 0), (40, 2), (60, 2), (80, 2)}


def read_rows(name):
    with (FIRST / name).open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def test_each_quality_and_sampling_reopens_same_marked_png(tmp_path, monkeypatch):
    png = stress.BASELINE / "astronaut_marked.png"
    real_open, real_save = Image.open, Image.Image.save
    opened, settings = [], []

    def observe_open(path, *args, **kwargs):
        opened.append(path)
        return real_open(path, *args, **kwargs)

    def observe_save(image, target, *args, **kwargs):
        assert Path(image.filename) == png and image.mode == "RGB"
        settings.append((kwargs["quality"], kwargs["subsampling"]))
        assert kwargs["format"] == "JPEG"
        assert not kwargs["progressive"] and not kwargs["optimize"]
        return real_save(image, target, *args, **kwargs)

    monkeypatch.setattr(Image, "open", observe_open)
    monkeypatch.setattr(Image.Image, "save", observe_save)
    for group, quality, sampling in stress.ATTACKS:
        target = tmp_path / f"{group}-{quality}.jpg"
        assert stress.encode(png, target, quality, sampling).shape == (512, 512, 3)
        assert opened[-2:] == [png, target]
        with real_open(target) as image:
            assert JpegImagePlugin.get_sampling(image) == sampling
    assert len(settings) == 6 and set(settings) == GRID


def test_separate_scores_recover_public_bit_order_without_payload():
    pixels = w0.load_rgb(FIRST / "astronaut_A_q10.jpg")
    expected, _ = w0.extract(pixels)
    scores, recovered, midpoint, gap, notices = stress.decision_scores(pixels)
    assert recovered == expected
    assert scores.shape == (32,)
    assert midpoint is not None and gap > 0 and not notices
    assert "".join(str(int(score > midpoint)) for score in scores) == expected


def test_archive_metrics_and_diagnostics():
    assert compare(FIRST, SECOND)["pass"]
    rows = read_rows("results.csv")
    scores = read_rows("decision_scores.csv")
    assert len(rows) == 18 and len(scores) == 18 * 32
    baseline = json.loads((stress.BASELINE / "manifest.json").read_text(encoding="utf-8"))
    assert {(row["image_id"], int(row["quality"]), int(row["pillow_subsampling"])) for row in rows} == {
        (entry["id"], q, s) for entry in baseline["inputs"]["images"] for q, s in GRID
    }
    for row in rows:
        original_bits, recovered = row["original_bits"], row["extracted_bits"]
        assert original_bits == w0.PAYLOAD and len(recovered) == 32 and set(recovered) <= {"0", "1"}
        wrong = [index for index, (a, b) in enumerate(zip(original_bits, recovered), 1) if a != b]
        assert json.loads(row["error_positions_1based"]) == wrong
        assert int(row["error_count"]) == len(wrong)
        assert int(row["total_bits"]) == 32 and float(row["ber"]) == len(wrong) / 32
        path = FIRST / row["file"]
        assert path.stat().st_size == int(row["bytes"]) and w0.digest(path) == row["sha256"]
        assert row["source_png"] == f'{row["image_id"]}_marked.png'
        assert row["source_png_sha256"] == baseline["files"][row["source_png"]]
        original = w0.load_rgb(w0.INPUTS / f'{row["image_id"]}.png')
        assert float(row["psnr_jpeg_vs_original_db"]) == pytest.approx(
            w0.psnr(original, w0.load_rgb(path)), abs=1e-10, rel=0
        )
        subset = [item for item in scores if all(item[key] == row[key]
                  for key in ("image_id", "quality", "subsampling"))]
        assert [int(item["position_1based"]) for item in subset] == list(range(1, 33))
        assert "".join(item["cluster_bit"] for item in subset) == recovered
        for item in subset:
            assert 0 <= float(item["score"]) <= 1
            if item["centroid_midpoint"]:
                margin = float(item["score"]) - float(item["centroid_midpoint"])
                assert float(item["signed_margin_to_midpoint"]) == pytest.approx(margin)
                assert str(int(margin > 0)) == item["cluster_bit"]
