"""G2 checks for parameter synchronization and archived paired evidence."""
from collections import defaultdict
import json
from pathlib import Path

import numpy as np
from PIL import Image, JpegImagePlugin
import pytest

from watermark_baseline import __main__ as w0
from watermark_baseline import g2, stress
from watermark_baseline.compare_runs import compare

FIRST = Path("outputs/run-g2")
SECOND = Path("outputs/run-g2-repeat")


@pytest.mark.parametrize("d2", [10, 20, 30])
def test_embed_and_public_extract_use_same_d2(tmp_path, monkeypatch, d2):
    real_factory = w0.new_watermark
    observations = []

    def factory():
        decoder = real_factory()
        embed, extract = decoder.embed, decoder.extract

        def observed_embed(**kwargs):
            observations.append(("embed", decoder.bwm_core.d1, decoder.bwm_core.d2))
            return embed(**kwargs)

        def observed_extract(**kwargs):
            observations.append(("extract", decoder.bwm_core.d1, decoder.bwm_core.d2))
            assert kwargs["mode"] == "bit" and kwargs["wm_shape"] == 32
            assert set(kwargs) == {"embed_img", "wm_shape", "mode"}
            return extract(**kwargs)

        decoder.embed = observed_embed
        decoder.extract = observed_extract
        return decoder

    monkeypatch.setattr(w0, "new_watermark", factory)
    path = tmp_path / "marked.png"
    w0.embed(w0.load_rgb(w0.INPUTS / "astronaut.png"), path, d2=d2)
    pixels = w0.load_rgb(path)
    bits, _ = w0.extract(pixels, d2=d2)
    assert observations == [("embed", 36, d2), ("extract", 36, d2)]
    scores, labels, *_ = stress.decision_scores(pixels, d2=d2)
    assert scores.shape == (32,) and labels == bits


def test_independent_jpeg_sources_and_fixed_grid(tmp_path, monkeypatch):
    real_encode = stress.encode
    calls = []
    out = tmp_path / "fresh"

    def observe(marked, target, q, sampling):
        assert marked.parent == target.parent == out
        assert target.name == f"{marked.stem}_q{q}.jpg"
        with Image.open(marked) as image:
            assert image.format == "PNG"
        calls.append((marked.name, q, sampling))
        return real_encode(marked, target, q, sampling)

    monkeypatch.setattr(stress, "encode", observe)
    g2.run(out)
    assert len(calls) == 27
    assert set(calls) == {(f"{image}_d2_{d}.png", q, 0)
                          for image in ("astronaut", "chelsea", "coffee")
                          for d in (10, 20, 30) for q in (10, 20, 30)}


def test_archived_pairs_and_scores():
    evidence = compare(FIRST, SECOND)
    assert evidence["pass"] and evidence["files_checked"] == 41
    manifest = json.loads((FIRST / "manifest.json").read_text(encoding="utf-8"))
    assert len(manifest["baseline_checks"]) == 12
    assert all(check["bits_and_psnr_match"] and check["sha256_match"] for check in manifest["baseline_checks"])
    rows = g2.read_csv(FIRST / "results.csv")
    paired = g2.read_csv(FIRST / "paired.csv")
    assert len(rows) == 36 and len(paired) == 24
    scores = defaultdict(list)
    for bit in g2.read_csv(FIRST / "decision_scores.csv"):
        scores[bit["image_id"], bit["d2"], bit["quality"]].append(bit)
    assert len(scores) == 36
    lookup = {}
    for row in rows:
        key = (row["image_id"], row["d2"], row["quality"])
        lookup[key] = row
        diagnostic = scores[key]
        expected, recovered = row["original_bits"], row["extracted_bits"]
        assert expected == w0.PAYLOAD and len(recovered) == 32 and set(recovered) <= {"0", "1"}
        wrong = [i for i, (a, b) in enumerate(zip(expected, recovered), 1) if a != b]
        assert json.loads(row["error_positions_1based"]) == wrong
        assert int(row["total_bits"]) == 32
        assert int(row["error_count"]) == len(wrong) and float(row["ber"]) == len(wrong) / 32
        assert [int(bit["position_1based"]) for bit in diagnostic] == list(range(1, 33))
        assert "".join(bit["cluster_bit"] for bit in diagnostic) == recovered
        means = [np.mean([float(bit["score"]) for bit, b in zip(diagnostic, expected) if b == label])
                 for label in "01"]
        assert float(row["mean_score_true_0"]) == pytest.approx(means[0])
        assert float(row["mean_score_true_1"]) == pytest.approx(means[1])
        assert (row["score_order_reversed"] == "True") == (means[0] > means[1])
        assert (row["all_bits_flipped"] == "True") == (len(wrong) == 32)
        original = w0.load_rgb(w0.INPUTS / f"{key[0]}.png")
        path = FIRST / row["file"]
        if row["quality"]:
            assert row["source_png"] == f"{key[0]}_d2_{key[1]}.png"
            with Image.open(path) as image:
                assert JpegImagePlugin.get_sampling(image) == 0
            assert float(row["psnr_jpeg_vs_original_db"]) == pytest.approx(
                w0.psnr(original, w0.load_rgb(path)), abs=1e-10, rel=0)
        else:
            assert float(row["psnr_marked_db"]) == pytest.approx(
                w0.psnr(original, w0.load_rgb(path)), abs=1e-10, rel=0)
    for pair in paired:
        i, d, q = (pair[field] for field in ("image_id", "d2", "quality"))
        candidate, baseline = lookup[i, d, q], lookup[i, "20", q]
        png_delta = float(candidate["psnr_marked_db"]) - float(baseline["psnr_marked_db"])
        assert float(pair["delta_png_psnr_db"]) == pytest.approx(png_delta)
        assert (pair["similar_png_psnr"] == "True") == (abs(png_delta) <= 1.0)
        assert float(pair["delta_ber"]) == float(candidate["ber"]) - float(baseline["ber"])
