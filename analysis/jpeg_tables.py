"""Cross-check the quantization tables of archived baseline grayscale JPEGs."""
from io import BytesIO

import numpy as np
from PIL import Image


def header_segments(payload):
    """Read marker segments before entropy-coded data."""
    if payload[:2] != b"\xff\xd8":
        raise ValueError("Missing JPEG SOI")
    pos = 2
    while pos < len(payload):
        if payload[pos] != 0xFF:
            raise ValueError("Expected JPEG header marker")
        while pos < len(payload) and payload[pos] == 0xFF:
            pos += 1
        if pos + 3 > len(payload):
            break
        marker = payload[pos]
        length = int.from_bytes(payload[pos + 1:pos + 3], "big")
        end = pos + 1 + length
        if length < 2 or end > len(payload):
            raise ValueError("Invalid JPEG header segment length")
        yield marker, payload[pos + 3:end]
        if marker == 0xDA:
            return
        pos = end
    raise ValueError("Missing JPEG SOS")


def from_zigzag(values):
    """Place DQT scan entries at (vertical frequency, horizontal frequency)."""
    matrix = np.empty((8, 8), dtype=np.int64)
    entries = iter(values)
    for diagonal in range(15):
        rows = range(max(0, diagonal - 7), min(7, diagonal) + 1)
        for k in rows if diagonal % 2 else reversed(rows):
            matrix[k, diagonal - k] = next(entries)
    return matrix


def verified_table(payload, shape):
    tables = {}
    frame = None
    for marker, data in header_segments(payload):
        if marker == 0xC0:
            if frame is not None or len(data) != 9 or data[0] != 8 or data[5] != 1:
                raise ValueError("Expected one 8-bit grayscale baseline JPEG frame")
            dimensions = (int.from_bytes(data[1:3], "big"), int.from_bytes(data[3:5], "big"))
            if dimensions != shape:
                raise ValueError(f"Unexpected JPEG dimensions: {dimensions}")
            frame = (data[6], data[7] >> 4, data[7] & 15, data[8])
        elif marker == 0xDB:
            if not data or len(data) % 65:
                raise ValueError("Expected complete 8-bit baseline DQT entries")
            for offset in range(0, len(data), 65):
                table_id = data[offset]
                raw = data[offset + 1:offset + 65]
                if table_id > 3 or table_id in tables or 0 in raw:
                    raise ValueError("Invalid or repeated baseline DQT table")
                tables[table_id] = raw
        elif marker == 0xDA:
            if frame is None or len(data) != 6 or data[:2] != bytes((1, frame[0])):
                raise ValueError("SOS does not identify the sole grayscale SOF0 component")

    table_id = frame[3]
    if table_id not in tables:
        raise ValueError(f"Missing DQT table {table_id} selected by the grayscale component")
    raw = tables[table_id]
    matrix = from_zigzag(raw)
    with Image.open(BytesIO(payload)) as image:
        if (image.format, image.mode, image.size) != ("JPEG", "L", shape[::-1]):
            raise ValueError("Pillow did not identify the expected grayscale JPEG")
        if image.layer != [frame]:
            raise ValueError("Pillow component and table selector disagree with SOF0")
        values = image.quantization.get(table_id)
        if values is None or len(values) != 64 or not np.array_equal(values, matrix.ravel()):
            raise ValueError("Pillow quantization order disagrees with raw DQT scan coordinates")
        image.load()
    return matrix, {
        "component_id": frame[0],
        "table_id": table_id,
        "precision_bits": 8,
        "shape": [8, 8],
        "raw_dqt_zigzag": list(raw),
        "natural_order": matrix.tolist(),
        "pillow_order": "row-major (vertical k, horizontal l), exactly matches independent DQT",
    }
