"""Exact pixel-domain PNG MSE for all 720 upstream SVD-QIM quantization steps.

This is intentionally an *exact* finite-domain reference method, not a
surrogate. It uses the same upstream encoder and OpenCV PNG byte encoder as
the actual JPEG evaluator, and measures the Pillow-decoded uint8 RGB pixels.
Unlike analytic coefficient distortion, ranking by this MSE exactly matches
the research protocol's PNG PSNR, including clipping and color conversion.

Expensive but scientifically useful: with the certified feasibility search,
the first clean-and-nine-QF pass is a PROVABLE global optimum on integer
d1=1..720 for the ORIGINAL RGB PNG PSNR objective.
"""
from __future__ import annotations

from io import BytesIO
from math import isfinite

import cv2
import numpy as np
from PIL import Image

from experiments import ori_qf_scan as fixed
from experiments.svd_qim_sweep import configured_instance
from experiments.spectral_certificate_qim import DOMAIN, D2


def encoded_upstream_rgb(rgb: np.ndarray, d1: int) -> np.ndarray:
    """The exact same 8-bit PNG pixels as wm.embed(filename='...png')."""
    if rgb.dtype != np.uint8 or rgb.ndim != 3 or rgb.shape[2] != 3:
        raise ValueError("Expected HxWx3 RGB uint8 image")
    if type(d1) is not int or d1 < 1:
        raise ValueError("Invalid d1")
    wm = configured_instance(d1, D2)
    wm.read_img(img=fixed.to_bgr(rgb))
    wm.read_wm([int(bit) for bit in fixed.PAYLOAD], mode="bit")
    pixels = wm.embed()
    ok, buffer = cv2.imencode(".png", pixels)
    if not ok:
        raise OSError("OpenCV PNG encoding failed")
    with Image.open(BytesIO(buffer.tobytes())) as image:
        decoded = np.asarray(image.convert("RGB"), dtype=np.uint8).copy()
    if decoded.shape != rgb.shape:
        raise AssertionError("Unexpected PNG shape")
    return decoded


def exact_png_rgb_mse_profile(
    rgb: np.ndarray,
    *,
    steps: tuple[int, ...] = DOMAIN,
) -> dict[int, float]:
    """Compute the REAL PNG MSE, not a smooth spectral approximation.

    For every candidate, uses original upstream embedding and actual PNG
    encoding, rather than assuming any continuity or monotonic relation to
    d1. It may be slower than 36-evaluation search by a large factor.
    """
    if (rgb.dtype != np.uint8 or rgb.ndim != 3 or rgb.shape[2] != 3 or
        not steps or len(set(steps)) != len(steps) or
        any(type(d) is not int or d < 1 for d in steps)):
        raise ValueError("Invalid RGB input or candidate domain")
    ref = rgb.astype(np.int16)
    result = {}
    for d1 in steps:
        png = encoded_upstream_rgb(rgb, d1).astype(np.int16)
        delta = ref - png
        # int16 squared arrays overflow; cast to float64 FIRST.
        mse = float(np.mean(np.square(delta.astype(np.float64)), dtype=np.float64))
        if not isfinite(mse) or mse < 0:
            raise AssertionError("Unexpected image MSE")
        result[d1] = mse
    return result
