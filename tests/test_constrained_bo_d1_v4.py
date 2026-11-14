"""Synthetic V4 policy regression tests. No real-JPEG superiority claim."""
import pytest

from experiments.auto_zero_ber import select_step as legacy_select_step
from experiments.constrained_bo_d1 import QFS
from experiments.constrained_bo_d1_v4 import INITIAL, WARM_START, select_step


def fake(d, *, feasible=None, fail_qf=5):
    if feasible is None:
        feasible = d >= 160 or d == 96
    checked = QFS if feasible else QFS[:QFS.index(fail_qf) + 1]
    errors = [0] * len(checked)
    if not feasible:
        errors[-1] = 1
    return {
        "png_psnr_db": 45.0 - d / 30.0,
        "clean_errors": 0,
        "worst_ber": 0.0 if feasible else 1 / 32,
        "jpeg_attacks": len(checked),
        "full_qf_verification": bool(feasible),
        "tested_qfs": ",".join(map(str, checked)),
        "qf_error_counts": ",".join(map(str, errors)),
    }


def test_phase_one_matches_unchanged_legacy_candidates():
    v4 = select_step(fake, budget=36)
    legacy = legacy_select_step(fake)
    a = [o.d1 for o in v4.observations[:WARM_START]]
    b = [o.d1 for o in legacy.measurements[:WARM_START]]
    assert a == b
    assert tuple(a[:len(INITIAL)]) == INITIAL
    assert v4.best_psnr_db >= max(
        o.psnr_db for o in v4.observations[:WARM_START]
        if o.verified_feasible
    )


def test_v4_budget_unique_verified_and_deterministic():
    first = select_step(fake, budget=36)
    second = select_step(fake, budget=36)
    assert first == second
    assert first.evaluations == 36
    assert len({o.d1 for o in first.observations}) == 36
    assert all(1 <= o.d1 <= 720 for o in first.observations)
    assert first.best_d1 in {o.d1 for o in first.observations if o.verified_feasible}
    assert first.best_psnr_db == max(
        o.psnr_db for o in first.observations if o.verified_feasible
    )
    assert any(r.startswith("feasible_boundary_warm_start") for r in first.reasons)
    assert any(r.startswith("bo_") for r in first.reasons)


def test_no_feasible_720_anchor_does_not_halt_search():
    result = select_step(lambda d: fake(d, feasible=(d == 96)), budget=16)
    assert result.evaluations == 16
    assert result.status in ("feasible", "no_verified_feasible")


def test_no_verified_success_is_reported():
    result = select_step(lambda d: fake(d, feasible=False), budget=16)
    assert result.evaluations == 16
    assert result.status == "no_verified_feasible"
    assert result.best_d1 is None


def test_every_candidate_feasible_includes_d1_1():
    result = select_step(lambda d: fake(d, feasible=True), budget=20)
    assert result.best_d1 == 1
    assert result.evaluations == 20


def test_false_qf_certificate_rejected():
    def bad(d):
        data = fake(d, feasible=True)
        data["qf_error_counts"] = "1,0,0,0,0,0,0,0,0"
        return data
    with pytest.raises(ValueError):
        select_step(bad, budget=8)


@pytest.mark.parametrize("budget", [0, 7, True, 721])
def test_invalid_budget(budget):
    with pytest.raises(ValueError):
        select_step(fake, budget=budget)
