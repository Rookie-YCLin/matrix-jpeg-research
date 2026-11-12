"""QIM decision margins and blind decoder interface contracts."""
import inspect

import numpy as np
import pytest

pytest.importorskip('blind_watermark')
from experiments.paper_low_qf import centered_decode, centered_quantize, decode, nearest_zero_quantize, nearest_zero_decode


@pytest.mark.parametrize('period', [90.0, 173.0])
@pytest.mark.parametrize('bit', [0, 1])
def test_quantized_values_survive_local_margin(period, bit):
    for value in [0, 1, 44.9, 45, 90, 180, 1000]:
        target = centered_quantize(value, period, bit, minimum=25)
        assert target >= 25
        for perturbation in [-0.249*period, 0, 0.249*period]:
            assert centered_decode(target+perturbation, period) == bit
        assert centered_decode(target+0.251*period, period) != bit


def test_ratio_invariance_only_when_unclamped():
    target = centered_quantize(500, 173, 1, minimum=173)
    for gain in [0.7, 1, 2]:
        assert centered_decode(gain*target, gain*173) == 1


def test_decoder_receives_neither_truth_nor_quality():
    assert list(inspect.signature(decode).parameters) == ['rgb', 'variant']


@pytest.mark.parametrize('bit', [0, 1])
def test_nearest_legal_lattice_and_margin(bit):
    for value in [0, 12, 44, 67, 100, 1000]:
        target = nearest_zero_quantize(value, 90, bit, minimum=15)
        candidates = np.array([90*(k+bit/2) for k in range(20)])
        candidates = candidates[candidates >= 15]
        assert abs(target-value) == pytest.approx(np.min(abs(candidates-value)))
        for error in [-22.4, 0, 22.4]:
            assert nearest_zero_decode(target+error, 90) == bit
