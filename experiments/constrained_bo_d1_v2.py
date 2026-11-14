"""CBO V2: feasibility-aware integer GP search, one d1; d2 stays fixed.

This is a predeclared experimental variant, not a proven improvement. It
matches the V2 comparator's integer domain and geometric initial design.
No untested QF is interpreted as a success; real-JPEG evaluator certifies it.
"""
from __future__ import annotations

from math import exp

import numpy as np
from scipy.stats import norm
from sklearn.gaussian_process import GaussianProcessClassifier, GaussianProcessRegressor
from sklearn.gaussian_process.kernels import Matern

from experiments.constrained_bo_d1 import Observation, Result, _parse

BOUNDS = (1, 720)
INITIAL = (720, 1, 4, 16, 64, 128, 256, 512)
BUDGET = 36
_OBJECTIVE_LENGTH = 0.12
_CLASSIFIER_LENGTH = 0.06
_FEASIBILITY_POWER = 4.0
_FAILURE_DISTANCE = 4.0
_COVERAGE_PERIOD = 4


def _scaled(values: np.ndarray) -> np.ndarray:
    return ((values - BOUNDS[0]) / (BOUNDS[1] - BOUNDS[0])).reshape(-1, 1)


def _model_scores(
    candidates: np.ndarray, observed: tuple[Observation, ...]
) -> tuple[np.ndarray, np.ndarray]:
    """Constrained EI scores and predicted P(full verified feasibility).

    The search uses a single joint success label for all QFs, not an
    independence product of separate QF models.
    """
    x = np.array([row.d1 for row in observed], dtype=float)
    y = np.array([row.psnr_db for row in observed], dtype=float)
    labels = np.array([int(row.verified_feasible) for row in observed])
    xx, qq = _scaled(x), _scaled(candidates.astype(float))
    surrogate = GaussianProcessRegressor(
        kernel=Matern(length_scale=_OBJECTIVE_LENGTH, nu=1.5),
        alpha=1e-5, normalize_y=True, optimizer=None,
    )
    surrogate.fit(xx, y)
    mu, sigma = surrogate.predict(qq, return_std=True)
    sigma = np.maximum(sigma, 1e-10)
    if np.unique(labels).size == 2:
        classifier = GaussianProcessClassifier(
            kernel=Matern(length_scale=_CLASSIFIER_LENGTH, nu=1.5),
            optimizer=None,
        )
        classifier.fit(xx, labels)
        pf = classifier.predict_proba(qq)[:, int(np.where(classifier.classes_ == 1)[0][0])]
    else:
        pf = np.full(len(candidates), 0.75 if labels[0] else 0.25)

    feasible_psnr = [o.psnr_db for o in observed if o.verified_feasible]
    distance_to_any = np.min(np.abs(candidates[:, None] - x[None, :]), axis=1)
    novelty = 1.0 - np.exp(-distance_to_any / 3.0)
    failed = x[labels == 0]
    if len(failed):
        distance_to_failed = np.min(np.abs(candidates[:, None] - failed[None, :]), axis=1)
        # Discourage repeatedly querying adjacent values of *known failing*
        # steps. Not a feasibility rule: every integer remains eligible.
        failure_repulsion = 1.0 - np.exp(-distance_to_failed / _FAILURE_DISTANCE)
    else:
        failure_repulsion = np.ones_like(pf)

    if feasible_psnr:
        best = max(feasible_psnr)
        delta = mu - best
        z = delta / sigma
        ei = np.maximum(delta * norm.cdf(z) + sigma * norm.pdf(z), 0.0)
        # Underpowered probability estimates caused V1 to repeatedly chase
        # implausibly high-PSNR infeasible low steps. Test a stronger but still
        # nonzero feasibility weighting, retaining periodic broad exploration.
        scores = ei * np.power(pf, _FEASIBILITY_POWER)
    else:
        scores = pf * (sigma + 0.05)

    scores *= (0.25 + 0.75 * novelty) * (0.05 + 0.95 * failure_repulsion)
    return scores, pf


def _interval_explorer(observed: tuple[Observation, ...]) -> int | None:
    """Probe unsampled interval midpoints without assuming BER monotonicity.

    A wide interval whose *both* endpoints fail can still contain a feasible
    island. Prioritize intervals below the current best feasible integer,
    where a smaller step can often improve image fidelity, but never rule out
    any region from the BO's subsequent acquisition evaluation.
    """
    rows = sorted(observed, key=lambda r: r.d1)
    feasible = [r for r in rows if r.verified_feasible]
    incumbent = max(feasible, key=lambda r: (r.psnr_db, -r.d1)).d1 if feasible else BOUNDS[1]
    gaps = []
    for left, right in zip(rows, rows[1:]):
        width = right.d1 - left.d1
        if width < 3:
            continue
        middle = (left.d1 + right.d1) // 2
        below = middle < incumbent
        transition = left.verified_feasible != right.verified_feasible
        both_infeasible = not left.verified_feasible and not right.verified_feasible
        # Feasible transitions and previously unsampled infeasible-infeasible
        # interiors are both useful. A wide gap is only *uncertainty*, not proof.
        tier = 2 if transition else 1 if both_infeasible else 0
        gaps.append((int(below), tier, width, -middle, middle))
    if not gaps:
        return None
    return max(gaps)[-1]


def select_step(evaluate, *, budget: int = BUDGET) -> Result:
    """Return best truly verified feasible step after unique real evaluations."""
    if type(budget) is not int or not len(INITIAL) <= budget <= BOUNDS[1]:
        raise ValueError("Invalid fixed integer evaluation budget")
    seen: dict[int, Observation] = {}
    reasons: list[str] = []

    def measure(d1: int, reason: str) -> None:
        if d1 in seen or not BOUNDS[0] <= d1 <= BOUNDS[1]:
            raise AssertionError("Duplicate or out-of-range candidate")
        seen[d1] = _parse(d1, evaluate(d1))
        reasons.append(reason)

    for d in INITIAL:
        measure(d, "same_as_v2_initialization")
    domain = np.arange(BOUNDS[0], BOUNDS[1] + 1, dtype=int)
    while len(seen) < budget:
        remaining = np.asarray([int(d) for d in domain if d not in seen], dtype=int)
        observed = tuple(seen.values())
        round_index = len(seen) - len(INITIAL) + 1
        if round_index % _COVERAGE_PERIOD == 0:
            point = _interval_explorer(observed)
            if point is not None and point in remaining:
                measure(point, "interval_feasibility_exploration")
                continue
        scores, _ = _model_scores(remaining, observed)
        chosen = int(remaining[int(np.argmax(scores))])
        measure(chosen, "failure_aware_constrained_ei")

    feasible = [o for o in seen.values() if o.verified_feasible]
    if not feasible:
        return Result("no_verified_feasible", None, None, tuple(seen.values()), tuple(reasons))
    best = max(feasible, key=lambda o: (o.psnr_db, -o.d1))
    return Result("feasible", best.d1, best.psnr_db, tuple(seen.values()), tuple(reasons))
