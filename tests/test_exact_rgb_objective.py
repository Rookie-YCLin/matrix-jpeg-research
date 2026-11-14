"""Verify that exhaustive RGB objective is pixel-identical to upstream PNG."""
from pathlib import Path

import numpy as np
from PIL import Image
import pytest

from experiments import ori_qf_scan as fixed
from experiments.exact_rgb_objective import (
    encoded_upstream_rgb, exact_png_rgb_mse_profile,
)
from experiments.svd_qim_sweep import configured_instance


def _small_rgb():
    rng = np.random.default_rng(2026)
    # 80x80 -> >=100 LL 4x4 blocks; enough to embed all 32 bits.
    return rng.integers(0, 256, size=(80, 80, 3), dtype=np.uint8)


@pytest.mark.parametrize("d", [1, 36, 96, 720])
def test_direct_encoded_pixels_match_upstream_png_exactly(tmp_path: Path, d):
    rgb = _small_rgb()
    direct = encoded_upstream_rgb(rgb, d)
    output = tmp_path / f"d{d}.png"
    wm = configured_instance(d, 20)
    wm.read_img(img=fixed.to_bgr(rgb))
    wm.read_wm([int(bit) for bit in fixed.PAYLOAD], mode="bit")
    wm.embed(filename=str(output))
    with Image.open(output) as source:
        official = np.asarray(source.convert("RGB"), dtype=np.uint8)
    assert np.array_equal(direct, official)


def test_exhaustive_rgb_profile_uses_true_pixel_mse():
    rgb = _small_rgb()
    steps = (1, 9, 96, 720)
    observed = exact_png_rgb_mse_profile(rgb, steps=steps)
    for d in steps:
        expected = np.mean(
            (rgb.astype(np.float64) -
             encoded_upstream_rgb(rgb, d).astype(np.float64)) ** 2
        )
        assert observed[d] == pytest.approx(expected, abs=1e-12)


def test_invalid_rgb_input_is_rejected():
    with pytest.raises(ValueError):
        exact_png_rgb_mse_profile(np.zeros((64, 64), dtype=np.uint8),steps=(1,))
