"""One-dimensional integer constrained Bayesian optimization for SVD-QIM d1.

Research pilot, not an optimality proof. Evaluator must return measured PNG
PSNR and actual full-nine-QF feasibility; partial JPEG checks only reject.
The implementation deliberately stays independent of watermark/JPEG imports.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Callable, Mapping

import numpy as np
from scipy.stats import norm
from sklearn.gaussian_process import GaussianProcessClassifier, GaussianProcessRegressor
from sklearn.gaussian_process.kernels import Matern

QFS = (5, 10, 15, 20, 30, 50, 70, 90, 95)
BOUNDS = (36, 720)
INITIAL = (36, 90, 150, 240, 400, 720)
BUDGET = 36


@dataclass(frozen=True)
class Observation:
    d1: int
    psnr_db: float
    clean_errors: int
    worst_observed_ber: float
    jpeg_attacks: int
    verified_feasible: bool


@dataclass(frozen=True)
class Result:
    status: str
    best_d1: int | None
    best_psnr_db: float | None
    observations: tuple[Observation, ...]
    reasons: tuple[str, ...]

    @property
    def evaluations(self) -> int:
        return len(self.observations)

    @property
    def jpeg_attacks(self) -> int:
        return sum(x.jpeg_attacks for x in self.observations)


def _parse(d1: int, row: Mapping[str, object]) -> Observation:
    """A positive result must have exactly nine *measured* successful QFs."""
    try:
        psnr = float(row["png_psnr_db"])
        clean = row["clean_errors"]
        ber = float(row["worst_ber"])
        attacks = row["jpeg_attacks"]
        verified = row["full_qf_verification"]
    except (KeyError, ValueError, TypeError, OverflowError) as exc:
        raise ValueError(f"Missing or malformed real measurement at d1={d1}") from exc
    if (
        not isfinite(psnr)
        or not isfinite(ber)
        or not 0 <= ber <= 1
        or type(clean) is not int
        or clean < 0
        or type(attacks) is not int
        or not 1 <= attacks <= len(QFS)
        or type(verified) is not bool
    ):
        raise ValueError(f"Invalid measurement at d1={d1}")
    if verified != (clean == 0 and ber == 0 and attacks == len(QFS)):
        raise ValueError(f"Inconsistent nine-QF certificate at d1={d1}")
    if "tested_qfs" in row:
        tested = tuple(int(q) for q in str(row["tested_qfs"]).split(","))
        if tested != QFS[:attacks]:
            raise ValueError(f"Actual QF order/coverage mismatch at d1={d1}")
    return Observation(d1, psnr, clean, ber, attacks, verified)


def _novelty(candidates: np.ndarray, sampled: np.ndarray) -> np.ndarray:
    """Normalized nearest-neighbour distance; helps find disconnected islands."""
    return np.min(
        np.abs(candidates[:, None] - sampled[None, :]), axis=1
    ) / float(BOUNDS[1] - BOUNDS[0])


def _acquisition(
    candidates: np.ndarray, observed: tuple[Observation, ...]
) -> tuple[np.ndarray, np.ndarray]:
    """EIC = expected PSNR improvement times modelled joint feasibility.

    Classification is trained on the *joint* all-QF success label: no
    unjustified conditional-independence assumption across JPEG qualities.
    Fixed kernel scales avoid repeated ML-II overfitting at tiny sample sizes.
    """
    x = np.asarray([o.d1 for o in observed], dtype=float)
    features = ((x - BOUNDS[0]) / (BOUNDS[1] - BOUNDS[0])).reshape(-1, 1)
    queries = ((candidates - BOUNDS[0]) / (BOUNDS[1] - BOUNDS[0])).reshape(-1, 1)
    y = np.asarray([o.psnr_db for o in observed], dtype=float)
    labels = np.asarray([int(o.verified_feasible) for o in observed], dtype=int)

    objective_gp = GaussianProcessRegressor(
        kernel=Matern(length_scale=0.12, nu=1.5),
        alpha=1e-5, normalize_y=True, optimizer=None,
    )
    objective_gp.fit(features, y)
    mean, std = objective_gp.predict(queries, return_std=True)
    std = np.maximum(std, 1e-12)

    if np.unique(labels).size == 2:
        classifier = GaussianProcessClassifier(
            kernel=Matern(length_scale=0.07, nu=1.5),
            optimizer=None, max_iter_predict=100,
        )
        classifier.fit(features, labels)
        positive_col = int(np.where(classifier.classes_ == 1)[0][0])
        pf = classifier.predict_proba(queries)[:, positive_col]
    else:
        # A classifier cannot be fitted to a single observed class.
        pf = np.full(len(candidates), 0.75 if labels[0] else 0.25)

    feasible_psnr = [o.psnr_db for o in observed if o.verified_feasible]
    novelty = _novelty(candidates, x)
    if not feasible_psnr:
        # No incumbent: seek likely feasible points, but maintain coverage.
        return pf * (0.25 + novelty), pf

    best = max(feasible_psnr)
    improvement = mean - best
    z = improvement / std
    ei = np.maximum(improvement * norm.cdf(z) + std * norm.pdf(z), 0.0)
    scores = ei * pf
    if not np.any(scores > 1e-14):
        scores = pf * novelty
    return scores, pf


def select_step(
    evaluate: Callable[[int], Mapping[str, object]],
    *,
    budget: int = BUDGET,
) -> Result:
    """Search d1 without presuming any fixed anchor is feasible.

    Output is always the *best actually measured feasible* point, never the
    GP's unverified prediction. No assumption of monotone BER or PSNR.
    """
    if type(budget) is not int or not len(INITIAL) <= budget <= (
        BOUNDS[1] - BOUNDS[0] + 1
    ):
        raise ValueError("Budget must cover the initialization and integer domain")
    measurements: dict[int, Observation] = {}
    reasons: list[str] = []

    def observe(d1: int, reason: str) -> None:
        if d1 in measurements:
            raise AssertionError("Duplicate expensive JPEG evaluation")
        measurements[d1] = _parse(d1, evaluate(d1))
        reasons.append(reason)

    for d in INITIAL:
        observe(d, "space_filling_initialization")

    all_candidates = np.arange(BOUNDS[0], BOUNDS[1] + 1, dtype=int)
    while len(measurements) < budget:
        candidates = np.asarray(
            [int(d) for d in all_candidates if d not in measurements], dtype=int
        )
        sampled = np.asarray(list(measurements), dtype=float)
        novelty = _novelty(candidates, sampled)
        if (len(measurements) - len(INITIAL) + 1) % 5 == 0:
            index, reason = int(np.argmax(novelty)), "coverage_exploration"
        else:
            observed = tuple(measurements.values())
            scores, _ = _acquisition(candidates, observed)
            index, reason = int(np.argmax(scores)), "constrained_ei"
        observe(int(candidates[index]), reason)

    feasible = [o for o in measurements.values() if o.verified_feasible]
    if not feasible:
        return Result("no_verified_feasible", None, None,
                      tuple(measurements.values()), tuple(reasons))
    best = max(feasible, key=lambda o: (o.psnr_db, -o.d1))
    return Result("feasible", best.d1, best.psnr_db,
                  tuple(measurements.values()), tuple(reasons))
