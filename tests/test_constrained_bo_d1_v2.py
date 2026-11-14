"""CBO V2 pre-registered synthetic policy checks; NOT JPEG performance evidence."""
import pytest

from experiments.constrained_bo_d1 import Observation
from experiments.constrained_bo_d1_v2 import (
    BOUNDS, INITIAL, _interval_explorer, select_step,
)
from experiments.constrained_bo_d1 import QFS


def fake(d, feasible=None):
    if feasible is None:
        feasible = 96 <= d <= 106 or d >= 160
    observed = QFS if feasible else (5,)
    return {
        "png_psnr_db": 47.0 - d / 30.0,
        "worst_ber": 0.0 if feasible else 1 / 32,
        "clean_errors": 0,
        "jpeg_attacks": len(observed),
        "tested_qfs": ",".join(str(q) for q in observed),
        "full_qf_verification": bool(feasible),
    }


def test_same_geometric_initial_design_as_v2_and_no_duplicate():
    calls = []
    result = select_step(lambda d: (calls.append(d), fake(d))[1], budget=18)
    assert tuple(calls[:len(INITIAL)]) == INITIAL
    assert len(calls) == len(set(calls)) == 18
    assert all(BOUNDS[0] <= d <= BOUNDS[1] for d in calls)
    assert result.best_d1 in calls
    assert fake(result.best_d1)["full_qf_verification"]


def test_deterministic_and_best_is_verified_and_not_inferred():
    one = select_step(fake, budget=20)
    two = select_step(fake, budget=20)
    assert one == two
    assert one.best_psnr_db == max(
        row.psnr_db for row in one.observations if row.verified_feasible
    )


def test_initial_anchor_can_fail_without_abandoning_search():
    result = select_step(lambda d: fake(d, feasible=(d == 96)), budget=16)
    assert result.evaluations == 16
    assert result.status in ("feasible", "no_verified_feasible")


def test_all_failed_is_honestly_reported():
    result = select_step(lambda d: fake(d, feasible=False), budget=16)
    assert result.status == "no_verified_feasible"
    assert result.best_d1 is None


def test_all_pass_case():
    result = select_step(lambda d: fake(d, feasible=True), budget=16)
    assert result.status == "feasible"
    assert result.best_d1 == 1


def test_disconnected_gap_is_explicitly_eligible_for_exploration():
    rows = tuple(
        Observation(d1=d, psnr_db=40-d/25, clean_errors=0,
                    worst_observed_ber=0 if d >= 256 else 1/32,
                    jpeg_attacks=9 if d >= 256 else 1,
                    verified_feasible=d >= 256)
        for d in INITIAL
    )
    # 64..128 both rejected, but 96 can still contain a small feasible island.
    assert _interval_explorer(rows, prefer_disconnected=True) == 96


def test_experiment_alternates_disconnected_exploration():
    result = select_step(fake, budget=25)
    assert "interval_feasibility_exploration" in result.reasons
    assert result.evaluations == 25


@pytest.mark.parametrize("invalid", [
    {"png_psnr_db": float("nan")},
    {"full_qf_verification": True, "jpeg_attacks": 1},
    {"full_qf_verification": True, "worst_ber": 1/32},
])
def test_invalid_success_certificates_fail_closed(invalid):
    def evaluator(d):
        row = fake(d, feasible=True)
        row.update(invalid)
        return row
    with pytest.raises(ValueError):
        select_step(evaluator, budget=8)


def test_invalid_budget():
    with pytest.raises(ValueError):
        select_step(fake, budget=7)
