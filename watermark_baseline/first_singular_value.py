"""Instance-local first-singular-value hard decision."""
from types import MethodType

from blind_watermark.bwm_core import dct, svd

from . import __main__ as w0


def block_get_wm_first(core, args):
    block, shuffler = args
    shuffled = dct(block).flatten()[shuffler].reshape(core.block_shape)
    _, singular_values, _ = svd(shuffled)
    return (singular_values[0] % core.d1 > core.d1 / 2) * 1


def new_decoder(method):
    decoder = w0.new_watermark()
    if method == "first":
        core = decoder.bwm_core
        core.block_get_wm_slow = MethodType(block_get_wm_first, core)
    elif method != "hard":
        raise ValueError(f"Unknown decoder: {method}")
    return decoder
