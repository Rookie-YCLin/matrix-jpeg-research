"""Tests for multi-image Grid runner without performing expensive JPEG calls."""
import csv
import json
from pathlib import Path

import numpy as np
from PIL import Image

from experiments import adaptive_d1_multimage_grid as target


def test_resume_skips_measured_d1(tmp_path, monkeypatch):
    images = tmp_path / "images"
    images.mkdir()
    Image.fromarray(np.zeros((16, 16, 3), dtype=np.uint8)).save(images / "a.png")
    output = tmp_path / "output"
    calls = []

    def fake_evaluate(rgb, d1, temporary):
        calls.append(d1)
        return d1

    def fake_summarise(result):
        d1 = result
        return [{
            "d1": d1, "mean_ber": 0.125, "worst_ber": 0.25,
            "png_psnr_db": 42.0, "png_mse_rgb_8bit": 1.0,
            "clean_errors": 0, "model_a_feasible": False,
            "model_b_lambda_0_5": 0.125 + d1 / 1000,
            "total_seconds": 0.0,
        }]

    monkeypatch.setattr(target, "evaluate_d1", fake_evaluate)
    monkeypatch.setattr(target, "summarise", fake_summarise)
    target.run(images, output, 1, 3)
    target.run(images, output, 1, 3)
    assert calls == [1, 2, 3]
    csv_path = next(output.glob("*/per_d1.csv"))
    with csv_path.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == 3
    assert [int(row["d1"]) for row in rows] == [1, 2, 3]
    metadata = json.loads(next(output.glob("*/source.json")).read_text())
    assert metadata["status"] == "complete"
    assert metadata["model_b_best_d1"] == 1


def test_resume_rejects_changed_domain(tmp_path, monkeypatch):
    images = tmp_path / "images"
    images.mkdir()
    Image.fromarray(np.zeros((16, 16, 3), dtype=np.uint8)).save(images / "a.png")
    output = tmp_path / "output"

    def fake_eval(rgb, d1, temp):
        return d1

    def fake_summary(d1):
        return [{
            "d1": d1, "mean_ber": 0.0, "worst_ber": 0.0,
            "png_psnr_db": 41.0, "png_mse_rgb_8bit": 0.0,
            "clean_errors": 0, "model_a_feasible": True,
            "model_b_lambda_0_5": 0.0, "total_seconds": 0.0,
        }]

    monkeypatch.setattr(target, "evaluate_d1", fake_eval)
    monkeypatch.setattr(target, "summarise", fake_summary)
    target.run(images, output, 1, 2)
    import pytest
    with pytest.raises(RuntimeError, match="Resume configuration mismatch"):
        target.run(images, output, 1, 3)
