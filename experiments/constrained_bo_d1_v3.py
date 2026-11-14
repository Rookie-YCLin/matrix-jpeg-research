"""CBO V3: partial-QF-aware constrained BO for integer SVD-QIM d1.

Research variant. The objective and the *joint* feasibility probability are
modelled separately; per-QF evidence is used for targeted exploration, NEVER
multiplied as if the nine outcomes were conditionally independent.

Only actually measured clean + nine-QF zero-error candidates can be selected.
Unmeasured QFs remain None (missing, not failures).
"""
from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Callable, Mapping

import numpy as np
from scipy.stats import norm
from sklearn.gaussian_process import GaussianProcessClassifier, GaussianProcessRegressor
from sklearn.gaussian_process.kernels import Matern

from experiments.constrained_bo_d1 import Observation, QFS, Result, _parse
from experiments.constrained_bo_d1_v2 import BOUNDS, INITIAL, BUDGET, _scaled

_OBJECTIVE_LENGTH = 0.12
_JOINT_LENGTH = 0.06
_QF_LOCAL_SCALE = 18.0  # d1 integers; deliberately shorter than the joint GP.
_COVERAGE_PERIOD = 4


@dataclass(frozen=True)
class Evidence:
    observation: Observation
    # Exactly nine slots in QFS order. None means NEVER MEASURED.
    qf_errors: tuple[int | None, ...]


def _parse_evidence(d1: int, row: Mapping[str, object]) -> Evidence:
    """Reject invented, internally inconsistent or incomplete certificates."""
    observation = _parse(d1, row)
    try:
        tested = tuple(int(v) for v in str(row["tested_qfs"]).split(","))
        errors_raw = str(row["qf_error_counts"]).split(",")
        if any(not token.isdigit() for token in errors_raw):
            raise ValueError("Noninteger QF error count")
        errors = tuple(int(token) for token in errors_raw)
    except (KeyError, ValueError, TypeError) as exc:
        raise ValueError(f"Missing per-QF measurement for d1={d1}") from exc
    n = observation.jpeg_attacks
    if tested != QFS[:n] or len(errors) != n or any(e < 0 for e in errors):
        raise ValueError(f"Invalid partial QF evidence at d1={d1}")
    if (max(errors) == 0) != (observation.worst_observed_ber == 0):
        raise ValueError(f"QF errors disagree with observed BER at d1={d1}")
    if observation.clean_errors == 0 and not observation.verified_feasible:
        # Streaming early rejection stops at first nonzero JPEG error.
        if errors[-1] == 0 or any(e != 0 for e in errors[:-1]):
            raise ValueError(f"Invalid early-rejection trace at d1={d1}")
    if observation.verified_feasible and (n != len(QFS) or any(errors)):
        raise ValueError(f"Invalid full-QF certificate at d1={d1}")
    return Evidence(observation, errors + (None,) * (len(QFS) - n))


def _surrogates(candidates: np.ndarray, observations: tuple[Evidence, ...]):
    """PSNR EI and a single joint-feasibility GPC; no QF independence."""
    x = np.array([e.observation.d1 for e in observations], dtype=float)
    y = np.array([e.observation.psnr_db for e in observations], dtype=float)
    labels = np.array([int(e.observation.verified_feasible) for e in observations])
    xx, qq = _scaled(x), _scaled(candidates.astype(float))
    objective = GaussianProcessRegressor(
        kernel=Matern(length_scale=_OBJECTIVE_LENGTH, nu=1.5),
        alpha=1e-5, normalize_y=True, optimizer=None,
    ).fit(xx, y)
    mean, std = objective.predict(qq, return_std=True)
    std = np.maximum(std, 1e-10)

    if np.unique(labels).size == 2:
        classifier = GaussianProcessClassifier(
            kernel=Matern(length_scale=_JOINT_LENGTH, nu=1.5),
            optimizer=None,
        ).fit(xx, labels)
        positive = int(np.where(classifier.classes_ == 1)[0][0])
        joint_probability = classifier.predict_proba(qq)[:, positive]
    else:
        joint_probability = np.full(len(candidates), 0.75 if labels[0] else 0.25)

    incumbents = [o.observation.psnr_db for o in observations
                  if o.observation.verified_feasible]
    if incumbents:
        improvement = mean - max(incumbents)
        z = improvement / std
        ei = np.maximum(improvement * norm.cdf(z) + std * norm.pdf(z), 0)
    else:
        # No observed feasible incumbent; seek objective uncertainty and feasibility.
        ei = std + 0.05
    return mean, std, ei, joint_probability


def _qf_information(candidates: np.ndarray, observations: tuple[Evidence, ...]):
    """Local Beta-Bernoulli variance from ACTUALLY observed QF outcomes.

    Kernel weights are fractional local pseudo-counts, not an independently
    calibrated likelihood. The score is an exploration heuristic, not the
    probability of all-nine-QF success.
    """
    scores = []
    for index in range(len(QFS)):
        rows = [(e.observation.d1, int(e.qf_errors[index] == 0))
                for e in observations if e.qf_errors[index] is not None]
        if rows:
            x = np.array([v[0] for v in rows], dtype=float)
            passed = np.array([v[1] for v in rows], dtype=float)
            weights = np.exp(-0.5 * (
                (candidates[:, None] - x[None, :]) / _QF_LOCAL_SCALE
            ) ** 2)
            successes = weights @ passed
            total = weights.sum(axis=1)
        else:
            successes = np.zeros(len(candidates))
            total = np.zeros(len(candidates))
        a = 1.0 + successes
        b = 1.0 + total - successes
        scores.append(a * b / ((a + b) ** 2 * (a + b + 1)))
    return np.mean(scores, axis=0)


def _qf_explorer(candidates: np.ndarray, observed: tuple[Evidence, ...],
                 mean: np.ndarray, std: np.ndarray) -> int:
    """Probe uncertain partial constraints where PNG quality might improve."""
    info = _qf_information(candidates, observed)
    best = max((e.observation.psnr_db for e in observed
                if e.observation.verified_feasible), default=None)
    if best is None:
        quality = np.ones_like(info)
    else:
        quality = 0.1 + 0.9 * norm.cdf((mean - best) / np.maximum(std, 1e-8))
    sampled = np.array([e.observation.d1 for e in observed])
    distance = np.min(np.abs(candidates[:, None] - sampled[None, :]), axis=1)
    # A soft, rather than hard, spread term: adjacent failures may hide success.
    spread = 0.5 + 0.5 * (1 - np.exp(-distance / 3.0))
    return int(candidates[int(np.argmax(info * quality * spread))])


def _gap_explorer(observed: tuple[Evidence, ...], remaining: np.ndarray,
                  *, prefer_disconnected: bool) -> int | None:
    """Explore any wide integer gap, even when both endpoints failed."""
    rows = sorted(observed, key=lambda e: e.observation.d1)
    feasible = [r.observation for r in rows if r.observation.verified_feasible]
    incumbent_d1 = max(feasible, key=lambda r: (r.psnr_db, -r.d1)).d1 if feasible else 720
    gaps: list[tuple[float, int]] = []
    for left, right in zip(rows, rows[1:]):
        lo, hi = left.observation.d1, right.observation.d1
        width = hi - lo
        if width <= 2:
            continue
        mid = (lo + hi) // 2
        if mid not in remaining:
            continue
        both_failed = not left.observation.verified_feasible and not right.observation.verified_feasible
        transition = left.observation.verified_feasible != right.observation.verified_feasible
        # Compare only QF labels actually measured at BOTH endpoints.
        qf_transitions = sum(
            a is not None and b is not None and (a == 0) != (b == 0)
            for a, b in zip(left.qf_errors, right.qf_errors)
        )
        tier = (2 if both_failed else 1 if transition else 0) if prefer_disconnected else (
            2 if transition else 1 if both_failed else 0
        )
        score = (3.0 if mid < incumbent_d1 else 0.0) + tier + min(width, 720) / 720
        score += 0.2 * qf_transitions
        gaps.append((score, mid))
    return max(gaps, key=lambda item: (item[0], -item[1]))[1] if gaps else None


def select_step(evaluate: Callable[[int], Mapping[str, object]],
                *, budget: int = BUDGET) -> Result:
    """Best fully verified point, with the original eight anchors and 36 budget."""
    if type(budget) is not int or not len(INITIAL) <= budget <= BOUNDS[1]:
        raise ValueError("Invalid fixed integer evaluation budget")
    evidence: dict[int, Evidence] = {}
    reasons: list[str] = []

    def measure(d: int, reason: str) -> None:
        if d in evidence or not BOUNDS[0] <= d <= BOUNDS[1]:
            raise AssertionError("Duplicate or out-of-range d1")
        evidence[d] = _parse_evidence(d, evaluate(d))
        reasons.append(reason)

    for anchor in INITIAL:
        measure(anchor, "same_as_v2_initialization")

    domain = np.arange(BOUNDS[0], BOUNDS[1] + 1, dtype=int)
    while len(evidence) < budget:
        remaining = np.array([int(d) for d in domain if d not in evidence], dtype=int)
        observed = tuple(evidence.values())
        round_number = len(evidence) - len(INITIAL) + 1
        if round_number % _COVERAGE_PERIOD == 0:
            chosen = _gap_explorer(
                observed, remaining,
                prefer_disconnected=(round_number // _COVERAGE_PERIOD) % 2 == 0,
            )
            if chosen is not None:
                measure(chosen, "partial_qf_gap_exploration")
                continue

        mean, std, ei, joint_p = _surrogates(remaining, observed)
        if round_number % _COVERAGE_PERIOD == 2:
            chosen = _qf_explorer(remaining, observed, mean, std)
            reason = "partial_qf_information_exploration"
        else:
            # Standard feasibility-weighted EI; NO power-of-four,
            # failure-neighbour penalty, or independent QF product.
            scores = ei * joint_p
            if not np.any(scores > 1e-14):
                scores = joint_p * (std + 0.05)
            chosen = int(remaining[int(np.argmax(scores))])
            reason = "joint_constrained_ei"
        measure(chosen, reason)

    measurements = tuple(e.observation for e in evidence.values())
    feasible = [r for r in measurements if r.verified_feasible]
    if not feasible:
        return Result("no_verified_feasible", None, None, measurements, tuple(reasons))
    winner = max(feasible, key=lambda r: (r.psnr_db, -r.d1))
    return Result("feasible", winner.d1, winner.psnr_db, measurements, tuple(reasons))
