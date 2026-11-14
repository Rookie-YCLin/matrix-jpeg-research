"""Synthetic-only BO policy tests (NOT real JPEG performance evidence)."""
import math

import pytest

from experiments.constrained_bo_d1 import INITIAL, QFS, select_step


def measurement(d, *, feasible=None, psnr=None, failed_at=5):
    if feasible is None:
        feasible = (96 <= d <= 105) or d >= 160
    checked = QFS if feasible else QFS[:QFS.index(failed_at) + 1]
    return {
        "png_psnr_db": (45 - d / 30) if psnr is None else psnr,
        "clean_errors": 0,
        "worst_ber": 0.0 if feasible else 1 / 32,
        "jpeg_attacks": len(checked),
        "full_qf_verification": bool(feasible),
        "tested_qfs": ",".join(map(str, checked)),
    }


def test_budget_unique_reproducible_feasible_and_certified():
    calls = []
    first = select_step(lambda d: (calls.append(d), measurement(d))[1], budget=16)
    second = select_step(measurement, budget=16)
    assert first == second
    assert first.status == "feasible"
    assert first.evaluations == 16
    assert len(calls) == len(set(calls))
    assert calls[:len(INITIAL)] == list(INITIAL)
    assert first.best_d1 in calls
    assert all(36 <= d <= 720 for d in calls)
    assert first.best_psnr_db == max(
        o.psnr_db for o in first.observations if o.verified_feasible
    )
    assert first.jpeg_attacks == sum(o.jpeg_attacks for o in first.observations)


def test_no_premature_anchor_rejection_and_no_feasible_outcome():
    all_bad = select_step(lambda d: measurement(d, feasible=False), budget=12)
    assert all_bad.status == "no_verified_feasible"
    assert all_bad.best_d1 is None
    assert all_bad.evaluations == 12
    # Even though the historical anchor 720 fails, still search.
    assert all_bad.observations[-1].d1 != 720


def test_all_feasible_works_with_one_class():
    result = select_step(lambda d: measurement(d, feasible=True), budget=12)
    assert result.status == "feasible"
    assert result.evaluations == 12
    assert result.best_d1 == 36


def test_candidate_set_covers_disconnected_island_without_monotone_assumption():
    # The algorithm must not assume that an infeasible gap proves all later
    # or earlier points infeasible. This test does not require finding the island.
    def islands(d):
        return measurement(d, feasible=(98 <= d <= 103 or d >= 500))
    outcome = select_step(islands, budget=20)
    assert outcome.evaluations == 20
    assert outcome.best_d1 is not None
    assert islands(outcome.best_d1)["full_qf_verification"]
    assert "coverage_exploration" in outcome.reasons


@pytest.mark.parametrize("changes", [
    {"png_psnr_db": float("nan")},
    {"clean_errors": -1},
    {"worst_ber": -0.25},
    {"jpeg_attacks": 0},
    {"full_qf_verification": True, "worst_ber": 1 / 32},
    {"full_qf_verification": True, "jpeg_attacks": 1},
    {"tested_qfs": "5,10", "jpeg_attacks": 9},
])
def test_invalid_or_false_certificate_rejected(changes):
    def invalid(d):
        row = measurement(d, feasible=True)
        row.update(changes)
        return row
    with pytest.raises(ValueError):
        select_step(invalid, budget=6)


def test_budget_restrictions():
    with pytest.raises(ValueError):
        select_step(measurement, budget=5)
    with pytest.raises(ValueError):
        select_step(measurement, budget=True)
