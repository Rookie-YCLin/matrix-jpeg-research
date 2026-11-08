"""G3 acceptance checks for the isolated decoder and frozen archives."""
from collections import defaultdict
import json
from pathlib import Path

import numpy as np
import pytest

from watermark_baseline import __main__ as w0
from watermark_baseline import g3, soft_decision, stress
from watermark_baseline.compare_runs import compare

FIRST = Path("outputs/run-g3")
SECOND = Path("outputs/run-g3-repeat")


def test_soft_score_anchors_period_and_bounds():
    assert soft_decision.soft_score(0.25) == pytest.approx(0)
    assert soft_decision.soft_score(0.75) == pytest.approx(1)
    r = np.linspace(-2, 2, 4097)
    scores = soft_decision.soft_score(r)
    assert np.all((scores >= 0) & (scores <= 1))
    np.testing.assert_allclose(soft_decision.soft_score(r + 1), scores, atol=1e-14, rtol=0)


def test_only_instance_block_decision_is_replaced(monkeypatch):
    hard = soft_decision.new_decoder("hard")
    soft = soft_decision.new_decoder("soft")
    assert type(hard) is type(soft) and type(hard.bwm_core) is type(soft.bwm_core)
    assert hard.extract.__func__ is soft.extract.__func__
    assert hard.extract_decrypt.__func__ is soft.extract_decrypt.__func__
    assert set(vars(soft.bwm_core)) - set(vars(hard.bwm_core)) == {"block_get_wm_slow"}
    assert soft.bwm_core.block_get_wm_slow.__func__ is soft_decision.block_get_wm_soft
    assert hard.bwm_core.block_get_wm_slow.__func__ is type(hard.bwm_core).block_get_wm_slow
    for name in ("block_get_wm", "read_img_arr", "extract", "extract_with_kmeans", "extract_avg", "embed"):
        assert getattr(hard.bwm_core, name).__func__ is getattr(soft.bwm_core, name).__func__
    assert (soft.bwm_core.d1, soft.bwm_core.d2, soft.bwm_core.fast_mode) == (36, 20, False)

    block = np.arange(16, dtype=np.float32).reshape(4, 4)
    shuffle = np.arange(15, -1, -1)
    expected = soft_decision.dct(block).flatten()[shuffle].reshape(4, 4)

    def observed_svd(matrix):
        np.testing.assert_array_equal(matrix, expected)
        return None, [27, 5, 0, 0], None

    monkeypatch.setattr(soft_decision, "svd", observed_svd)
    assert soft.bwm_core.block_get_wm((block, shuffle)) == pytest.approx(0.75)


def test_fresh_run_uses_same_pixels_and_never_embeds_or_encodes(tmp_path, monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("An archive-only decoder experiment attempted embedding or JPEG encoding")

    monkeypatch.setattr(w0, "embed", forbidden)
    monkeypatch.setattr(stress, "encode", forbidden)
    calls = []
    real_extract = g3.extract

    def observed(pixels, method):
        calls.append((pixels, method, pixels.copy()))
        return real_extract(pixels, method)

    monkeypatch.setattr(g3, "extract", observed)
    g3.run(tmp_path / "fresh")
    assert len(calls) == 24
    for hard, soft in zip(calls[::2], calls[1::2]):
        assert (hard[1], soft[1]) == ("hard", "soft")
        assert hard[0] is soft[0]
        np.testing.assert_array_equal(hard[2], soft[2])


def test_archived_metrics_and_labels():
    evidence = compare(FIRST, SECOND)
    assert evidence["pass"] and evidence["files_checked"] == 5
    manifest = json.loads((FIRST / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["archive_only"] and manifest["historical_hard_rows_verified"] == 12
    rows = g3.read_csv(FIRST / "results.csv")
    scores = defaultdict(list)
    for bit in g3.read_csv(FIRST / "decision_scores.csv"):
        scores[bit["image_id"], bit["condition"], bit["method"]].append(bit)
    assert len(rows) == len(scores) == 24
    combined = defaultdict(int)
    pairs = defaultdict(list)
    for row in rows:
        expected, recovered = row["original_bits"], row["extracted_bits"]
        assert expected == w0.PAYLOAD and len(recovered) == 32 and set(recovered) <= {"0", "1"}
        errors = [i for i, (a, b) in enumerate(zip(expected, recovered), 1) if a != b]
        assert json.loads(row["error_positions_1based"]) == errors
        assert int(row["error_count"]) == len(errors)
        assert int(row["total_bits"]) == 32 and float(row["ber"]) == len(errors) / 32
        assert w0.digest(Path(row["input_path"])) == manifest["images"][row["input_path"]] == row["input_sha256"]
        bit_rows = scores[row["image_id"], row["condition"], row["method"]]
        assert [int(bit["position_1based"]) for bit in bit_rows] == list(range(1, 33))
        assert "".join(bit["cluster_bit"] for bit in bit_rows) == recovered
        assert "".join(bit["original_bit"] for bit in bit_rows) == expected
        means = [np.mean([float(bit["score"]) for bit in bit_rows if bit["original_bit"] == label])
                 for label in "01"]
        assert float(row["mean_score_true_0"]) == pytest.approx(means[0])
        assert float(row["mean_score_true_1"]) == pytest.approx(means[1])
        assert (row["score_order_reversed"] == "True") == (means[0] > means[1])
        assert (row["all_bits_flipped"] == "True") == (len(errors) == 32)
        pairs[row["image_id"], row["condition"]].append(row)
        combined[row["condition"], row["method"]] += len(errors)
    assert len(pairs) == 12
    for hard, soft in pairs.values():
        assert (hard["method"], soft["method"]) == ("hard", "soft")
        for key in ("input_path", "input_sha256", "psnr_vs_original_db"):
            assert hard[key] == soft[key]
    summary = g3.read_csv(FIRST / "summary.csv")
    assert len(summary) == 8
    for row in summary:
        errors = combined[row["condition"], row["method"]]
        assert int(row["error_count"]) == errors
        assert int(row["total_bits"]) == 96 and float(row["ber"]) == errors / 96
    assert combined["Q10", "hard"] == 12
