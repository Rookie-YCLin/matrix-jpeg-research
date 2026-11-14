"""CBO V3 synthetic unit tests. Not evidence of real JPEG performance."""
import numpy as np
import pytest

from experiments.constrained_bo_d1 import QFS
from experiments.constrained_bo_d1_v3 import (
    BOUNDS, INITIAL, _parse_evidence, _qf_information, _failure_saturation, select_step,
)


def fake(d, *, feasible=None, fail_qf=5):
    if feasible is None:
        feasible = (96 <= d <= 98) or d >= 160
    tested = QFS if feasible else QFS[:QFS.index(fail_qf) + 1]
    errors = (0,) * len(tested) if feasible else (0,) * (len(tested) - 1) + (1,)
    return {
        "png_psnr_db": 46 - d / 35,
        "clean_errors": 0,
        "worst_ber": 0.0 if feasible else 1 / 32,
        "jpeg_attacks": len(tested),
        "tested_qfs": ",".join(map(str, tested)),
        "qf_error_counts": ",".join(map(str, errors)),
        "full_qf_verification": bool(feasible),
    }


def test_actual_qf_prefix_only_untested_is_missing():
    row = _parse_evidence(99, fake(99, feasible=False, fail_qf=20))
    assert row.qf_errors == (0, 0, 0, 1, None, None, None, None, None)
    assert not row.observation.verified_feasible


def test_failed_qf5_does_not_label_unmeasured_qfs_as_failed():
    row = _parse_evidence(99, fake(99, feasible=False))
    assert row.qf_errors == (1,) + (None,) * 8
    assert not row.observation.verified_feasible


def test_auxiliary_qf_model_uses_failure_stage():
    qf5 = (_parse_evidence(99, fake(99, feasible=False, fail_qf=5)),)
    qf20 = (_parse_evidence(99, fake(99, feasible=False, fail_qf=20)),)
    near = np.array([99, 100], dtype=int)
    assert not np.allclose(_qf_information(near, qf5),
                           _qf_information(near, qf20))


def test_same_initialization_budget_unique_deterministic_and_verified():
    seen = []
    first = select_step(lambda d: (seen.append(d), fake(d))[1], budget=16)
    second = select_step(fake, budget=16)
    assert first == second
    assert tuple(seen[:len(INITIAL)]) == INITIAL
    assert len(seen) == len(set(seen)) == 16
    assert all(BOUNDS[0] <= d <= BOUNDS[1] for d in seen)
    assert first.best_d1 in seen
    assert first.best_psnr_db == max(o.psnr_db for o in first.observations
                                    if o.verified_feasible)
    assert "partial_qf_information_exploration" in first.reasons
    assert "partial_qf_gap_exploration" in first.reasons
    assert "joint_constrained_ei" in first.reasons


def test_all_failed_does_not_claim_feasibility():
    outcome = select_step(lambda d: fake(d, feasible=False), budget=12)
    assert outcome.status == "no_verified_feasible"
    assert outcome.best_d1 is None
    assert outcome.evaluations == 12


def test_all_passed_one_class():
    outcome = select_step(lambda d: fake(d, feasible=True), budget=12)
    assert outcome.status == "feasible"
    assert outcome.best_d1 == 1


@pytest.mark.parametrize("change", [
    {"qf_error_counts": ""},
    {"qf_error_counts": "0,0"},
    {"qf_error_counts": "x"},
    {"tested_qfs": "5,15,10,20,30,50,70,90,95"},
    {"full_qf_verification": True, "jpeg_attacks": 1},
    {"full_qf_verification": True, "qf_error_counts": "1,0,0,0,0,0,0,0,0"},
    {"png_psnr_db": float("nan")},
])
def test_false_certificate_or_missing_measurement_fails_closed(change):
    row = fake(160, feasible=True)
    row.update(change)
    with pytest.raises(ValueError):
        _parse_evidence(160, row)


def test_false_prefix_before_early_rejection_rejected():
    row = fake(99, feasible=False, fail_qf=20)
    row["qf_error_counts"] = "0,1,0,1"
    with pytest.raises(ValueError):
        _parse_evidence(99, row)


@pytest.mark.parametrize("budget", [0, 7, 721, True])
def test_invalid_budget(budget):
    with pytest.raises(ValueError):
        select_step(fake, budget=budget)


def test_failure_saturation_needs_three_same_qf_local_failures():
    rows = tuple(_parse_evidence(d, fake(d, feasible=False)) for d in (1, 2, 4, 16))
    scores = _failure_saturation(np.array([3, 98], dtype=int), rows)
    assert 0 < scores[0] < 0.1
    assert scores[1] == 1.0

    # One failed candidate is NOT sufficient reason to suppress a neighbor.
    single = (_parse_evidence(99, fake(99, feasible=False)),)
    assert _failure_saturation(np.array([96], dtype=int), single)[0] == 1.0


def test_success_offsets_local_penalty_and_different_qf_failures_do_not_stack():
    observations = tuple(_parse_evidence(d, fake(d, feasible=False)) for d in (95, 99, 100))
    near = np.array([98], dtype=int)
    assert _failure_saturation(near, observations)[0] < 1.0
    with_success = observations + (_parse_evidence(96, fake(96, feasible=True)),)
    assert _failure_saturation(near, with_success)[0] == 1.0

    different_stages = (
        _parse_evidence(95, fake(95, feasible=False, fail_qf=5)),
        _parse_evidence(99, fake(99, feasible=False, fail_qf=10)),
        _parse_evidence(100, fake(100, feasible=False, fail_qf=20)),
    )
    assert _failure_saturation(near, different_stages)[0] == 1.0


def test_repeated_failed_low_d1_does_not_consume_entire_budget():
    outcome = select_step(lambda d: fake(d, feasible=(96 <= d <= 98 or d >= 160)), budget=36)
    low_failures = sum(o.d1 <= 15 and not o.verified_feasible for o in outcome.observations)
    assert low_failures <= 11  # Guardrail, not evidence of image-level performance.
    assert outcome.evaluations == 36
    assert len({o.d1 for o in outcome.observations}) == 36
