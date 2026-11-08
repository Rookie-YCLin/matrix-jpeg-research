"""Synthetic gates for the zero-phase candidate, runnable before image trials."""
import itertools

import numpy as np
import pytest
from cv2 import idct

from watermark_baseline import __main__ as w0
from watermark_baseline.ordered_embedding import new_embedder, ordered_pair


@pytest.mark.parametrize("bit", [0, 1])
def test_global_optimum_against_exhaustive_grid(bit):
    rng = np.random.default_rng(51)
    spectra = [
        (0, 0, 0), (22, 22, 15), (40, 19, 18), (27, 0, 0),
        (45, 15, 15), (100, 100, 100), (10_000, 10_000, 10_000),
        (50, 26, np.nextafter(25., np.inf)),
    ]
    spectra.extend(np.sort(rng.integers(0, 1024, (120, 3)), axis=1)[:, ::-1])
    for x, y, z in spectra:
        a0, a1 = 36 * (0.25 + bit / 2), 20 * (0.25 + bit / 2)
        grid0 = np.arange(a0, x + 100, 36)
        grid1 = np.arange(a1, y + 100, 20)
        expected = min(((a - x)**2 + (b - y)**2, a, b) for a, b in itertools.product(grid0, grid1)
                       if a >= b >= z)
        pair = ordered_pair((x, y, z), bit)
        assert pair == expected[1:]
        assert pair[0] >= pair[1] >= z >= 0
        assert (pair[0] % 36, pair[1] % 20) == (a0, a1)


def test_tie_and_quality_cost():
    assert ordered_pair((27, 0, 0), 0) == (9, 5)
    assert ordered_pair((45, 15, 0), 0) == (45, 5)
    for s, bit in [([100, 60, 40, 1], 0), ([22, 22, 15, 1], 0), ([0, 0, 0, 0], 1)]:
        q = np.array([*ordered_pair(s, bit), *s[2:]])
        old = np.array(s, dtype=float)
        old[:2] = (old[:2] // [36, 20] + 0.25 + bit / 2) * [36, 20]
        u, _ = np.linalg.qr(np.arange(16).reshape(4, 4) + np.eye(4))
        v = u[::-1]
        original = (u * s) @ v.T
        for modified in (q, old):
            changed = (u * modified) @ v.T
            assert np.linalg.norm(changed - original, "fro") ** 2 == pytest.approx(
                np.sum((modified - s) ** 2))
    assert ordered_pair((22, 22, 15), 0) == (45, 25)
    assert (45 - 22)**2 + (25 - 22)**2 > (9 - 22)**2 + (25 - 22)**2
    assert (117 - 100)**2 + (65 - 60)**2 < (81 - 100)**2 + (65 - 60)**2


@pytest.mark.parametrize("bit", [0, 1])
def test_recomputed_svd_and_actual_upstream_block_reader(bit):
    rng = np.random.default_rng(64)
    embedder = new_embedder()
    embedder.read_wm([bit], mode="bit")
    core = embedder.bwm_core
    decoder = w0.new_watermark().bwm_core
    assert type(core) is type(decoder)
    assert set(vars(core)) - set(vars(decoder)) <= {"block_add_wm_slow", "wm_bit"}
    assert core.block_get_wm_slow.__func__ is decoder.block_get_wm_slow.__func__
    for name in ("read_img_arr", "embed", "extract_raw", "extract_avg", "extract_with_kmeans"):
        assert getattr(core, name).__func__ is getattr(decoder, name).__func__
    for s in ([0, 0, 0, 0], [22, 22, 15, 0], [40, 19, 18, 18], [180, 180, 180, 179]):
        u, _ = np.linalg.qr(rng.normal(size=(4, 4)))
        v, _ = np.linalg.qr(rng.normal(size=(4, 4)))
        matrix = (u * s) @ v.T
        q = [*ordered_pair(s, bit), *s[2:]]
        np.testing.assert_allclose(np.linalg.svd((u * q) @ v.T, compute_uv=False), q, atol=1e-12)
        shuffle = rng.permutation(16)
        flat = np.empty(16, dtype=np.float32)
        flat[shuffle] = matrix.flatten()
        block = idct(flat.reshape(4, 4))
        marked = core.block_add_wm_slow((block, shuffle, 0))
        assert decoder.block_get_wm_slow((marked, shuffle)) == bit
