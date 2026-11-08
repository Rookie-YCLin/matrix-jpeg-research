"""Exact nearest ordered bit-coset pair for the fixed upstream steps."""
from types import MethodType

import numpy as np
from blind_watermark.bwm_core import dct, idct, svd

from . import __main__ as w0


def ordered_pair(s, bit):
    """Minimize squared change, breaking ties by smaller q0, then q1."""
    if bit not in (0, 1):
        raise ValueError("Expected a binary bit")
    x, y, z = map(float, s[:3])
    if not np.isfinite([x, y, z]).all() or not x >= y >= z >= 0:
        raise ValueError("Expected finite nonnegative descending singular values")
    ratios = [value.as_integer_ratio() for value in (x, y, z)]
    scale = max(denominator for _, denominator in ratios)
    x, y, z = (numerator * (scale // denominator) for numerator, denominator in ratios)
    a0, a1 = 9 + 18 * bit, 5 + 10 * bit

    # A feasible upward-rounded pair costs less than 20² + 56² < 60².
    # Any optimum must therefore have |q1 - s1| < 60.
    step1 = 20 * scale
    first = max(0, -((a1 * scale - max(z, y - 60 * scale)) // step1))
    last = (y + (60 - a1) * scale) // step1
    best = None
    for k1 in range(first, last + 1):
        q1 = a1 + 20 * k1
        floor_k0 = (x - a0 * scale) // (36 * scale)
        min_k0 = max(0, -((a0 - q1) // 36))
        for k0 in (max(min_k0, floor_k0), max(min_k0, floor_k0 + 1)):
            q0 = a0 + 36 * k0
            trial = ((q0 * scale - x) ** 2 + (q1 * scale - y) ** 2, q0, q1)
            if best is None or trial < best:
                best = trial
    return best[1:]


def ordered_block(core, arg):
    block, shuffler, index = arg
    matrix = dct(block).flatten()[shuffler].reshape(core.block_shape)
    u, s, vh = svd(matrix)
    bit = int(core.wm_bit[index % core.wm_size])
    pair = ordered_pair(s, bit)
    s[:2] = pair
    if tuple(map(float, s[:2])) != pair:
        raise ValueError("Upstream dtype cannot represent the selected bit lattice")
    flat = np.dot(u, np.dot(np.diag(s), vh)).flatten()
    flat[shuffler] = flat.copy()
    return idct(flat.reshape(core.block_shape))


def new_embedder():
    embedder = w0.new_watermark()
    core = embedder.bwm_core
    core.block_add_wm_slow = MethodType(ordered_block, core)
    return embedder
