"""G4 acceptance checks for the isolated decoder and frozen archives."""
from collections import defaultdict
import json
from pathlib import Path

import numpy as np
import pytest

from watermark_baseline import __main__ as w0
from watermark_baseline import g4, first_singular_value, stress
from watermark_baseline.compare_runs import compare

FIRST = Path("outputs/run-g4")
SECOND = Path("outputs/run-g4-repeat")


def test_only_instance_block_decision_is_replaced(monkeypatch):
    hard = first_singular_value.new_decoder("hard")
    first = first_singular_value.new_decoder("first")
    assert type(hard) is type(first) and type(hard.bwm_core) is type(first.bwm_core)
    assert hard.extract.__func__ is first.extract.__func__
    assert hard.extract_decrypt.__func__ is first.extract_decrypt.__func__
    assert set(vars(first.bwm_core)) - set(vars(hard.bwm_core)) == {"block_get_wm_slow"}
    assert first.bwm_core.block_get_wm_slow.__func__ is first_singular_value.block_get_wm_first
    assert hard.bwm_core.block_get_wm_slow.__func__ is type(hard.bwm_core).block_get_wm_slow
    for name in ("block_get_wm", "read_img_arr", "extract", "extract_with_kmeans", "extract_avg", "embed"):
        assert getattr(hard.bwm_core, name).__func__ is getattr(first.bwm_core, name).__func__
    assert (first.bwm_core.d1, first.bwm_core.d2, first.bwm_core.fast_mode) == (36, 20, False)

    block = np.arange(16, dtype=np.float32).reshape(4, 4)
    shuffle = np.arange(15, -1, -1)
    expected = first_singular_value.dct(block).flatten()[shuffle].reshape(4, 4)

    singular_values = [27, 5, 0, 0]

    def observed_svd(matrix):
        np.testing.assert_array_equal(matrix, expected)
        return None, singular_values, None

    monkeypatch.setattr(first_singular_value, "svd", observed_svd)
    assert first.bwm_core.block_get_wm((block, shuffle)) == 1
    singular_values[1] = 15
    assert first.bwm_core.block_get_wm((block, shuffle)) == 1
    singular_values[0] = 18
    assert first.bwm_core.block_get_wm((block, shuffle)) == 0
    singular_values[0] = 63
    assert first.bwm_core.block_get_wm((block, shuffle)) == 1


def test_fresh_run_uses_same_pixels_and_never_embeds_or_encodes(tmp_path, monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("An archive-only decoder experiment attempted embedding or JPEG encoding")

    monkeypatch.setattr(w0, "embed", forbidden)
    monkeypatch.setattr(stress, "encode", forbidden)
    calls = []
    real_extract = g4.extract

    def observed(pixels, method):
        calls.append((pixels, method, pixels.copy()))
        return real_extract(pixels, method)

    monkeypatch.setattr(g4, "extract", observed)
    g4.run(tmp_path / "fresh")
    assert len(calls) == 24
    for hard, first in zip(calls[::2], calls[1::2]):
        assert (hard[1], first[1]) == ("hard", "first")
        assert hard[0] is first[0]
        np.testing.assert_array_equal(hard[2], first[2])


def test_archived_metrics_and_labels():
    evidence = compare(FIRST, SECOND)
    assert evidence["pass"] and evidence["files_checked"] == 7
    manifest = json.loads((FIRST / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["archive_only"] and manifest["historical_hard_rows_verified"] == 12
    rows = g4.read_csv(FIRST / "results.csv")
    scores = defaultdict(list)
    for bit in g4.read_csv(FIRST / "decision_scores.csv"):
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
    for hard, first in pairs.values():
        assert (hard["method"], first["method"]) == ("hard", "first")
        for key in ("input_path", "input_sha256", "psnr_vs_original_db"):
            assert hard[key] == first[key]
    summary = g4.read_csv(FIRST / "summary.csv")
    assert len(summary) == 8
    for row in summary:
        errors = combined[row["condition"], row["method"]]
        assert int(row["error_count"]) == errors
        assert int(row["total_bits"]) == 96 and float(row["ber"]) == errors / 96
    assert combined["Q10", "hard"] == 12

def test_paired_differences_and_block_flip_rates():
    rows = g4.read_csv(FIRST / "results.csv")
    bits = {(r["image_id"], r["condition"], r["method"]): r["extracted_bits"] for r in rows}
    paired = g4.read_csv(FIRST / "paired_bits.csv")
    assert len(paired) == 384
    assert len({(r["image_id"], r["condition"], r["position_1based"]) for r in paired}) == 384
    for row in paired:
        key = row["image_id"], row["condition"]
        index = int(row["position_1based"]) - 1
        assert row["hard_bit"] == bits[*key, "hard"][index]
        assert row["first_bit"] == bits[*key, "first"][index]
        assert (row["changed"] == "True") == (row["hard_bit"] != row["first_bit"])

    stability = g4.read_csv(FIRST / "block_stability.csv")
    assert len(stability) == 12
    for row in stability:
        blocks = int(row["blocks_per_channel"])
        channels = [int(row[f"flips_{name}"]) for name in "yuv"]
        assert all(0 <= count <= blocks for count in channels)
        assert int(row["total_votes"]) == 3 * blocks
        assert int(row["flips"]) == sum(channels)
        assert float(row["flip_rate"]) == sum(channels) / (3 * blocks)
        if row["condition"] == "PNG":
            assert sum(channels) == 0
