"""Instance-local SVD soft decision for the pinned upstream common decoder."""
from types import MethodType

import numpy as np
from blind_watermark.bwm_core import dct, svd

from . import __main__ as w0


def soft_score(remainder):
    return (1 - np.sin(2 * np.pi * remainder)) / 2


def block_get_wm_soft(core, args):
    block, shuffler = args
    # Identical DCT, permutation and SVD inputs to upstream block_get_wm_slow.
    shuffled = dct(block).flatten()[shuffler].reshape(core.block_shape)
    _, singular_values, _ = svd(shuffled)
    r0 = (singular_values[0] % core.d1) / core.d1
    r1 = (singular_values[1] % core.d2) / core.d2
    return (3 * soft_score(r0) + soft_score(r1)) / 4


def new_decoder(method):
    decoder = w0.new_watermark()
    if method == "soft":
        core = decoder.bwm_core
        core.block_get_wm_slow = MethodType(block_get_wm_soft, core)
    elif method != "hard":
        raise ValueError(f"Unknown decoder: {method}")
    return decoder
