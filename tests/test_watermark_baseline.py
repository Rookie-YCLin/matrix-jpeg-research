"""Acceptance checks for the fixed W0 wrapper and archived data."""
import csv
from hashlib import sha256
import json
from pathlib import Path

import numpy as np
from PIL import Image
import pytest

from watermark_baseline import __main__ as w0


def test_fixed_payload_order_and_public_decoder(tmp_path, monkeypatch):
    rgb = w0.load_rgb(w0.INPUTS / "astronaut.png")
    target = tmp_path / "marked.png"
    assert w0.embed(rgb, target) == 4096

    real = w0.new_watermark
    calls = []

    def factory():
        decoder = real()
        upstream_extract = decoder.extract

        def observed(**kwargs):
            assert set(kwargs) == {"embed_img", "wm_shape", "mode"}
            assert kwargs["wm_shape"] == 32
            assert kwargs["mode"] == "bit"
            calls.append(decoder)
            return upstream_extract(**kwargs)

        decoder.extract = observed
        return decoder

    monkeypatch.setattr(w0, "new_watermark", factory)
    marked = w0.load_rgb(target)
    for _ in range(2):
        assert w0.extract(marked) == ("10110010111001000101101011010001", [])
    assert len(calls) == 2 and calls[0] is not calls[1]


def test_rgb_bgr_and_metrics():
    rgb = np.array([[[255, 1, 3]]], dtype=np.uint8)
    assert w0.to_bgr(rgb).tolist() == [[[3, 1, 255]]]
    assert w0.psnr(rgb, rgb) == float("inf")
    assert w0.psnr(np.zeros_like(rgb), np.full_like(rgb, 255)) == 0
    assert w0.compare_bits("0" * 32, "1" + "0" * 30 + "1") == ([1, 32], 2 / 32)
    with pytest.raises(ValueError):
        w0.compare_bits("0" * 32, "0" * 31)


def test_png_failure_stops_all_jpeg(tmp_path, monkeypatch):
    def embed(rgb, target):
        Image.fromarray(rgb).save(target)
        return 4096

    def attack(*args):
        pytest.fail("JPEG ran despite failed PNG gate")

    monkeypatch.setattr(w0, "embed", embed)
    monkeypatch.setattr(w0, "extract", lambda _: ("0" * 32, []))
    monkeypatch.setattr(w0, "encode_attack", attack)
    out = tmp_path / "blocked"
    assert not w0.run(out)
    assert json.loads((out / "manifest.json").read_text())["status"] == "png_gate_failed"
    with (out / "results.csv").open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == 3 and all(row["attack"] == "none" for row in rows)


def test_each_attack_reopens_same_png(tmp_path, monkeypatch):
    png = w0.INPUTS / "astronaut.png"
    original_open = w0.Image.open
    opened = []

    def observed(path, *args, **kwargs):
        opened.append(path)
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(w0.Image, "open", observed)
    for quality in w0.QUALITIES:
        target = tmp_path / f"q{quality}.jpg"
        assert w0.encode_attack(png, target, quality).shape == (512, 512, 3)
        assert opened[-2:] == [png, target]


def test_archived_results():
    out = Path("outputs/run-w0")
    manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["status"] == "complete"
    assert manifest["inputs"] == json.loads((w0.INPUTS / "inputs.json").read_text(encoding="utf-8"))
    for name, digest in manifest["files"].items():
        assert sha256((out / name).read_bytes()).hexdigest() == digest
    with (out / "results.csv").open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    expected = {(entry["id"], q) for entry in manifest["inputs"]["images"]
                for q in ("", "40", "60", "80", "95")}
    assert len(rows) == len(expected)
    assert {(row["image_id"], row["quality"]) for row in rows} == expected
    for row in rows:
        image_id, q = row["image_id"], row["quality"]
        assert row["original_bits"] == w0.PAYLOAD
        assert set(row["extracted_bits"]) <= {"0", "1"}
        errors, ber = w0.compare_bits(row["original_bits"], row["extracted_bits"])
        assert json.loads(row["error_positions_1based"]) == errors
        assert int(row["error_count"]) == len(errors)
        assert int(row["total_bits"]) == 32 and float(row["ber"]) == ber
        original = w0.load_rgb(w0.INPUTS / f"{image_id}.png")
        marked = w0.load_rgb(out / f"{image_id}_marked.png")
        assert float(row["psnr_marked_db"]) == pytest.approx(w0.psnr(original, marked), abs=1e-10, rel=0)
        path = out / row["file"]
        assert int(row["bytes"]) == path.stat().st_size
        assert row["sha256"] == manifest["files"][path.name]
        if q:
            assert row["attack"] == "jpeg"
            assert float(row["psnr_jpeg_vs_original_db"]) == pytest.approx(
                w0.psnr(original, w0.load_rgb(path)), abs=1e-10, rel=0
            )
        else:
            assert row["attack"] == "none" and ber == 0 and json.loads(row["warnings"]) == []
