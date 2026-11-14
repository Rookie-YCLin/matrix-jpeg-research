"""CBO V4: verified-feasibility warm start followed by constrained integer BO.

A diagnostic alternative to the repeatedly failing low-d1 EI strategies:
reuse the deterministic *selection policy* from legacy V2 for the first 18
actual evaluations, then allocate the remaining 18 (36 total) to BO. The
real evaluator, joint nine-QF hard certificate and all missing-QF rules are
unchanged. This is a hybrid BO policy, not a pure-GP acquisition theorem.
"""
from __future__ import annotations

from typing import Callable, Mapping

import numpy as np

from experiments.auto_zero_ber import Measurement as LegacyMeasurement
from experiments.auto_zero_ber import _next_candidate as _legacy_next_candidate
from experiments.constrained_bo_d1 import Observation, Result
from experiments.constrained_bo_d1_v3 import (
    BOUNDS, INITIAL, BUDGET, Evidence, _parse_evidence,
    _gap_explorer, _surrogates, _qf_explorer, _failure_saturation,
)

WARM_START = 18  # 8 shared anchors + 10 legacy V2 feasibility refinements.


def _legacy_measurements(observed: tuple[Evidence, ...]) -> dict[int, LegacyMeasurement]:
    """Adapt ONLY actual observed values to the unchanged V2 selector.

    The stricter V4 evidence parser ensures that the legacy `feasible`
    predicate agrees with the fully verified nine-QF certificate.
    """
    converted: dict[int, LegacyMeasurement] = {}
    for item in observed:
        o = item.observation
        legacy = LegacyMeasurement(
            d1=o.d1, worst_ber=o.worst_observed_ber,
            clean_errors=o.clean_errors, psnr_db=o.psnr_db,
        )
        if legacy.feasible != o.verified_feasible:
            raise AssertionError("Partial-QF result misread as feasible")
        converted[o.d1] = legacy
    return converted


def select_step(evaluate: Callable[[int], Mapping[str, object]],
                *, budget: int = BUDGET) -> Result:
    """Find the best actually nine-QF-verified candidate, with no duplicate d1."""
    if type(budget) is not int or not len(INITIAL) <= budget <= BOUNDS[1]:
        raise ValueError("Invalid fixed integer evaluation budget")
    evidence: dict[int, Evidence] = {}
    reasons: list[str] = []
    domain = np.arange(BOUNDS[0], BOUNDS[1] + 1, dtype=int)

    def measure(d1: int, reason: str):
        if d1 in evidence or not BOUNDS[0] <= d1 <= BOUNDS[1]:
            raise AssertionError("Duplicate or out-of-domain candidate")
        evidence[d1] = _parse_evidence(d1, evaluate(d1))
        reasons.append(reason)

    for d1 in INITIAL:
        measure(d1, "same_as_legacy_v2_initialization")

    # Phase I: cheaply establish a *measured* feasible boundary, rather
    # than asking EI to prioritize indefinitely the very small, failing d1.
    while len(evidence) < min(WARM_START, budget):
        observed = tuple(evidence.values())
        remaining = np.array([int(d) for d in domain if d not in evidence], dtype=int)
        if any(item.observation.verified_feasible for item in observed):
            legacy_data = _legacy_measurements(observed)
            d1, legacy_reason = _legacy_next_candidate(
                legacy_data, len(evidence) - len(INITIAL)
            )
            if d1 not in remaining:
                raise AssertionError("Legacy warm start proposed a duplicate")
            measure(int(d1), "feasible_boundary_warm_start:" + legacy_reason)
        else:
            # Do NOT assume d1=720 is eligible on every image.
            _, _, ei, joint = _surrogates(remaining, observed)
            chosen = int(remaining[int(np.argmax(ei * joint))])
            measure(chosen, "no_feasible_incumbent_search")

    # Phase II: use the remaining budget for GP-based quality improvement,
    # partial QF information and disconnected-island exploration.
    while len(evidence) < budget:
        remaining = np.array([int(d) for d in domain if d not in evidence], dtype=int)
        observed = tuple(evidence.values())
        round_number = len(evidence) - min(WARM_START, budget) + 1
        if round_number % 4 == 0:
            d1 = _gap_explorer(
                observed, remaining,
                prefer_disconnected=(round_number // 4) % 2 == 0,
            )
            if d1 is not None:
                measure(d1, "bo_disconnected_gap_probe")
                continue
        mean, std, ei, joint = _surrogates(remaining, observed)
        if round_number % 4 == 2:
            d1 = _qf_explorer(remaining, observed, mean, std)
            reason = "bo_partial_qf_information_probe"
        else:
            scores = ei * joint * _failure_saturation(remaining, observed)
            if not np.any(scores > 1e-14):
                scores = joint * (std + 0.05) * _failure_saturation(remaining, observed)
            d1 = int(remaining[int(np.argmax(scores))])
            reason = "bo_constrained_ei"
        measure(d1, reason)

    measurements: tuple[Observation, ...] = tuple(
        item.observation for item in evidence.values()
    )
    valid = [o for o in measurements if o.verified_feasible]
    if not valid:
        return Result("no_verified_feasible", None, None, measurements, tuple(reasons))
    best = max(valid, key=lambda o: (o.psnr_db, -o.d1))
    return Result("feasible", best.d1, best.psnr_db, measurements, tuple(reasons))
