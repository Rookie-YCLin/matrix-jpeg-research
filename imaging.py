"""Lossless input, display export, and an actual JPEG round trip."""
from io import BytesIO
from math import inf, log10

import numpy as np
from PIL import Image

JPEG_SETTINGS = {"quality": 80, "optimize": False, "progressive": False}


def read_gray_png(payload):
    with Image.open(BytesIO(payload)) as image:
        if image.mode != "L" or image.format != "PNG":
            raise ValueError("Expected an 8-bit grayscale PNG (mode L)")
        return np.array(image)


def save_display(matrix, path):
    pixels = np.clip(np.rint(matrix), 0, 255).astype(np.uint8)
    Image.fromarray(pixels).save(path)


def jpeg_round_trip(pixels, path):
    Image.fromarray(pixels).save(path, format="JPEG", **JPEG_SETTINGS)
    with Image.open(path) as image:
        if image.format != "JPEG" or image.mode != "L":
            raise ValueError("Expected a grayscale JPEG")
        decoded = np.array(image, dtype=np.float64)
    if decoded.shape != pixels.shape:
        raise ValueError("JPEG round trip changed image dimensions")
    return decoded


def quality_metrics(original, decoded):
    mse = float(np.mean((original - decoded) ** 2))
    psnr = 10 * log10(255**2 / mse) if mse else inf
    return mse, psnr
