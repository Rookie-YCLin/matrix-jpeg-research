"""Spectral-Certificate QIM: exact finite-domain optimum for transform distortion.

Unlike EI/GP heuristics, this algorithm derives its objective from the upstream
4x4 shuffled-DCT SVD-QIM construction. Under orthogonal SVD/DCT/Haar operations,
each block's squared coefficient perturbation is exactly
    (sigma1_quantized(d1)-sigma1)^2 + (sigma2_quantized(d2)-sigma2)^2.

Evaluate this objective for *every* integer d1=1..720 BEFORE any expensive JPEG
checks. Then test candidates in provably optimal distortion order, stopping at
the first genuinely clean-and-nine-JPEG-QF-zero-BER candidate. Since all
lower-distortion candidates have already been tested and rejected, the result
is globally optimal over this finite search space FOR THE TRANSFORM-DOMAIN
DISTORTION METRIC.

This does NOT establish a global optimum for uint8 RGB PNG PSNR: RGB conversion,
pixel clipping and rounding change the pixel-domain objective. The actual PNG
PSNR of each evaluated candidate is separately measured and reported.

The original upstream embedder, fixed payload/keys, d2=20 and Pillow JPEG are
not modified. No surrogate GP, constraint independence or BER monotonicity.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Callable, Mapping

import numpy as np

DOMAIN = tuple(range(1, 721))
D2 = 20
QFS = (5, 10, 15, 20, 30, 50, 70, 90, 95)


@dataclass(frozen=True)
class SpectralCertificate:
    status: str
    best_d1: int | None
    best_transform_energy: float | None
    best_png_psnr_db: float | None
    # Ordered real, independently verified calls to the expensive evaluator.
    attempted_steps: tuple[int, ...]
    evaluated: tuple[dict, ...]
    # True only for a fully measured successful candidate preceded by all
    # other candidates with better spectral energy (including exact ties).
    certified: bool

    @property
    def evaluations(self) -> int:
        return len(self.attempted_steps)


def spectral_energies(
    sigma0: np.ndarray,
    sigma1: np.ndarray,
    watermark_bits: np.ndarray,
    steps: tuple[int, ...] = DOMAIN,
    *,
    d2: int = D2,
    chunk: int = 64,
) -> dict[int, float]:
    """Compute exact squared Frobenius distortion of the SVD-QIM coefficients.

    Inputs are the *original*, shuffled-DCT singular values, not post-watermark
    singular values. watermark_bits must match upstream's block assignment
    AFTER upstream password_wm permutation. Each triple corresponds to one
    embedded 4x4 block (repeated across all 3 image channels).

    Chunked broadcasting uses O(N_blocks*chunk) memory; the entire 720-step
    profile requires no JPEG encoding, extraction, or GP fitting.
    """
    s0 = np.asarray(sigma0, dtype=np.float64)
    s1 = np.asarray(sigma1, dtype=np.float64)
    bits = np.asarray(watermark_bits)
    steps = tuple(steps)
    if (s0.ndim != 1 or s1.shape != s0.shape or bits.shape != s0.shape
        or not len(s0) or not np.isfinite(s0).all() or not np.isfinite(s1).all()
        or np.any(s0 < 0) or np.any(s1 < 0)
        or not np.isin(bits, [0, 1]).all()
        or type(d2) is not int or d2 <= 0
        or type(chunk) is not int or chunk < 1
        or not steps or len(set(steps)) != len(steps)
        or any(type(d) is not int or d < 1 for d in steps)):
        raise ValueError("Invalid singular-value profile or candidate domain")
    offset = 0.25 + 0.5 * bits.astype(np.float64)
    target_s1 = (np.floor(s1 / d2) + offset) * d2
    fixed_energy = float(np.dot(target_s1 - s1, target_s1 - s1))
    result = {}
    for start in range(0, len(steps), chunk):
        ds = np.asarray(steps[start:start+chunk], dtype=np.float64)
        targets = (np.floor(s0[:, None] / ds[None, :])
                   + offset[:, None]) * ds[None, :]
        deltas = targets - s0[:, None]
        energies = np.sum(deltas * deltas, axis=0, dtype=np.float64) + fixed_energy
        for d, energy in zip(ds.astype(int), energies):
            result[int(d)] = float(energy)
    return result


def upstream_spectral_profile(rgb: np.ndarray, *, steps: tuple[int, ...] = DOMAIN
                              ) -> dict[int, float]:
    """Read exactly the same original 4x4 shuffled-DCT SVD blocks as guofei.

    Uses the pinned public API and the pinned core's random block permutation.
    Does not mutate upstream files or change the quantization rule.
    """
    import cv2
    from blind_watermark.bwm_core import random_strategy1
    from experiments.ori_qf_scan import PAYLOAD, to_bgr
    from experiments.svd_qim_sweep import configured_instance

    if rgb.dtype != np.uint8 or rgb.ndim != 3 or rgb.shape[2] != 3:
        raise ValueError("Expected an RGB uint8 image")
    wm = configured_instance(36, D2)
    wm.read_img(img=to_bgr(rgb))
    wm.read_wm([int(bit) for bit in PAYLOAD], mode="bit")
    core = wm.bwm_core
    if core.fast_mode or tuple(core.block_shape) != (4, 4):
        raise AssertionError("Pinned upstream slow shuffled 4x4 SVD only")
    core.init_block_index()
    if core.block_num < len(PAYLOAD) + 1:
        raise AssertionError("Insufficient image blocks for this payload")
    shuffles = random_strategy1(core.password_img, core.block_num, 16)
    bit_per_block = np.asarray(core.wm_bit)[
        np.arange(core.block_num, dtype=int) % core.wm_size
    ]
    sigma0, sigma1 = [], []
    for channel in range(3):
        for i, (row, col) in enumerate(core.block_index):
            block = core.ca_block[channel][row, col]
            shuffled = cv2.dct(block).flatten()[shuffles[i]].reshape((4, 4))
            # Use the same SVD routine as pinned upstream; singular values
            # before modifying either d1 or d2.
            _, s, _ = np.linalg.svd(shuffled)
            sigma0.append(float(s[0]))
            sigma1.append(float(s[1]))
    bits = np.tile(bit_per_block, 3)
    return spectral_energies(
        np.asarray(sigma0), np.asarray(sigma1), bits,
        steps=steps, d2=D2,
    )


def _validate_real_certificate(d1: int, data: Mapping[str, object]) -> dict:
    """Fail closed: never infer skipped JPEG qualities as successes."""
    from experiments.constrained_bo_d1_v3 import _parse_evidence
    evidence = _parse_evidence(d1, data)
    row = evidence.observation
    return {
        "d1": d1,
        "png_psnr_db": row.psnr_db,
        "clean_errors": row.clean_errors,
        "jpeg_attacks": row.jpeg_attacks,
        "verified_feasible": row.verified_feasible,
        "qf_error_counts": evidence.qf_errors,
    }


def select_certified(
    transform_energies: Mapping[int, float],
    evaluate: Callable[[int], Mapping[str, object]],
    *,
    max_evaluations: int = len(DOMAIN),
    objective: str = "spectral",
) -> SpectralCertificate:
    """Return the global spectral optimum when feasible, never a GP prediction.

    Before the first verified feasible candidate, each lower-energy candidate
    is actually rejected by a clean or JPEG bit error. This is an elementary
    order-statistics certificate requiring NO smoothness or monotonicity.

    If the budget stops before a success, return *uncertified* without claiming
    infeasibility; full 720-step exhaustion is required to prove nonexistence.
    """
    if objective not in ("spectral", "rgb_mse"):
        raise ValueError("objective must be spectral or rgb_mse")
    if (type(max_evaluations) is not int or
        not 1 <= max_evaluations <= len(DOMAIN)):
        raise ValueError("max_evaluations must be in 1..720")
    if set(transform_energies) != set(DOMAIN):
        raise ValueError("Every integer d1=1..720 must have a spectral score")
    for d, value in transform_energies.items():
        if (type(d) is not int or
            not isinstance(value, (float, int, np.floating)) or
            not isfinite(float(value)) or float(value) < 0):
            raise ValueError("Spectral scores must be nonnegative and finite")

    ranked = sorted(DOMAIN, key=lambda d: (float(transform_energies[d]), d))
    attempted: list[int] = []
    observations: list[dict] = []
    for d1 in ranked[:max_evaluations]:
        parsed = _validate_real_certificate(d1, evaluate(d1))
        attempted.append(d1)
        observations.append(parsed)
        if parsed["verified_feasible"]:
            return SpectralCertificate(
                status=f"certified_{objective}_global_optimum",
                best_d1=d1,
                best_transform_energy=float(transform_energies[d1]),
                best_png_psnr_db=parsed["png_psnr_db"],
                attempted_steps=tuple(attempted),
                evaluated=tuple(observations),
                certified=True,
            )
    return SpectralCertificate(
        status=("certified_no_feasible_in_domain" if
                max_evaluations == len(DOMAIN) else "evaluation_budget_exhausted"),
        best_d1=None, best_transform_energy=None, best_png_psnr_db=None,
        attempted_steps=tuple(attempted),
        evaluated=tuple(observations),
        certified=(max_evaluations == len(DOMAIN)),
    )
