"""Check complete paired evidence and replay the trial in Research CI."""
import csv
import json
from pathlib import Path

import pytest
from PIL import Image, JpegImagePlugin

from watermark_baseline import __main__ as w0
from watermark_baseline import ordered_trial, stress
from watermark_baseline.compare_runs import compare

FIRST = Path("outputs/run-g5-ordered")
SECOND = Path("outputs/run-g5-ordered-repeat")


def rows(file):
    with (FIRST / file).open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def test_fresh_trial_uses_independent_matching_pngs(tmp_path, monkeypatch):
    real_encode = stress.encode
    observed = set()

    def encode(png, jpeg, quality, sampling):
        assert jpeg.parent == png.parent and jpeg.name == f"{png.stem}_q{quality}.jpg"
        assert png.suffix == ".png" and sampling == 0
        key = png.name, quality
        assert key not in observed
        observed.add(key)
        return real_encode(png, jpeg, quality, sampling)

    monkeypatch.setattr(stress, "encode", encode)
    ordered_trial.run(tmp_path / "trial")
    assert len(observed) == 18


def test_saved_evidence_and_paired_quality():
    comparison = compare(FIRST, SECOND)
    assert comparison["pass"] and comparison["files_checked"] == 28
    manifest = json.loads((FIRST / "manifest.json").read_text(encoding="utf-8"))
    assert len(manifest["baseline_checks"]) == 12
    assert all(row["bit_and_psnr_match"] for row in manifest["baseline_checks"])
    assert manifest["png_psnr_limits_db"] == [0.5, 1.0]
    measurements = rows("results.csv")
    table = {(r["image_id"], r["quality"], r["method"]): r for r in measurements}
    assert len(measurements) == len(table) == 24
    for row in measurements:
        assert row["original_bits"] == w0.PAYLOAD
        assert len(row["extracted_bits"]) == 32 and set(row["extracted_bits"]) <= {"0", "1"}
        errors = [i for i, (a, b) in enumerate(zip(row["original_bits"], row["extracted_bits"]), 1) if a != b]
        assert json.loads(row["error_positions_1based"]) == errors
        assert int(row["error_count"]) == len(errors)
        assert int(row["total_bits"]) == 32 and float(row["ber"]) == len(errors) / 32
        path = FIRST / row["file"]
        assert w0.digest(path) == row["sha256"]
        png = FIRST / row["source_png"]
        assert w0.digest(png) == row["source_png_sha256"]
        original = w0.load_rgb(w0.INPUTS / f'{row["image_id"]}.png')
        assert float(row["psnr_marked_db"]) == pytest.approx(
            w0.psnr(original, w0.load_rgb(png)), rel=0, abs=1e-10)
        if row["quality"]:
            assert float(row["psnr_jpeg_vs_original_db"]) == pytest.approx(
                w0.psnr(original, w0.load_rgb(path)), rel=0, abs=1e-10)
            with Image.open(path) as image:
                assert JpegImagePlugin.get_sampling(image) == 0

    paired = rows("paired.csv")
    assert len(paired) == 12
    for row in paired:
        key = row["image_id"], row["quality"]
        original, candidate = table[*key, "original"], table[*key, "ordered"]
        delta = float(candidate["psnr_marked_db"]) - float(original["psnr_marked_db"])
        assert float(row["delta_png_psnr_db"]) == pytest.approx(delta)
        assert (row["within_0_5_db"] == "True") == (abs(delta) <= 0.5)
        assert (row["within_1_0_db"] == "True") == (abs(delta) <= 1.0)
        assert float(row["delta_ber"]) == float(candidate["ber"]) - float(original["ber"])

    ordering = rows("ordering.csv")
    assert len(ordering) == 108
    raw = [r for r in ordering if r["stage"] == "quantized_index_order"]
    assert sum(int(r["top_inversion"]) for r in raw if r["method"] == "original") == 57
    assert sum(int(r["lower_inversion"]) for r in raw if r["method"] == "original") == 2027
    assert all(int(r[key]) == 0 for r in raw if r["method"] == "ordered"
               for key in ("top_inversion", "lower_inversion", "negative_values",
                           "first_vote_errors", "second_vote_errors"))
