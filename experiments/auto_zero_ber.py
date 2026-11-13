"""Automatic zero-BER-first search for the discrete SVD-QIM step d1.

User-facing operation is select_step(evaluate): no d1, grid, bounds, or
candidate tuning is requested. The historical d1=720 is a predeclared,
verified-on-a-per-image-basis eligibility anchor, NOT a universal guarantee.

The optimizer is an empirical black-box method. It makes no monotonic-BER
assumption and has no global-optimality guarantee. The evaluation callback
must use the same image, payload, JPEG settings, and complete target-QF set.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Callable, Mapping

# Research protocol constants, deliberately not part of the user-facing API.
_ANCHOR = 720
_BUDGET = 36
_PROBES = (1, 4, 16, 64, 128, 256, 512)
_EXPLORE_PERIOD = 5


@dataclass(frozen=True)
class Measurement:
    d1: int
    worst_ber: float
    clean_errors: int
    psnr_db: float

    @property
    def feasible(self) -> bool:
        return self.worst_ber == 0 and self.clean_errors == 0


@dataclass(frozen=True)
class SearchOutcome:
    status: str
    best_d1: int | None
    best_psnr_db: float | None
    measurements: tuple[Measurement, ...]
    reasons: tuple[str, ...]

    @property
    def evaluations(self) -> int:
        return len(self.measurements)


def _measurement(d1: int, values: Mapping[str, object]) -> Measurement:
    try:
        ber = float(values['worst_ber'])
        clean = int(values['clean_errors'])
        psnr = float(values['png_psnr_db'])
    except (KeyError, TypeError, ValueError, OverflowError) as exc:
        raise ValueError(f'Invalid measurement at d1={d1}') from exc
    if not 0 <= ber <= 1 or not isfinite(ber) or clean < 0 or not isfinite(psnr):
        raise ValueError(f'Invalid BER, clean errors, or PSNR at d1={d1}')
    return Measurement(d1, ber, clean, psnr)


def _midpoint_candidates(seen: Mapping[int, Measurement]) -> list[tuple[int, int, int, int]]:
    """Return unmeasured interval midpoints: (left, right, candidate, tier)."""
    ordered = sorted(seen)
    mids = []
    for a, b in zip(ordered, ordered[1:]):
        if b - a <= 1:
            continue
        fa, fb = seen[a].feasible, seen[b].feasible
        # Rank transitions first; never assume the interior is monotonic.
        tier = 0 if fa != fb else 1 if fa and fb else 2
        mids.append((a, b, (a + b) // 2, tier))
    return mids


def _next_candidate(seen: Mapping[int, Measurement], step: int) -> tuple[int, str]:
    mids = _midpoint_candidates(seen)
    if not mids:
        remaining = [d for d in range(1, _ANCHOR) if d not in seen]
        if not remaining:
            raise RuntimeError('No unmeasured candidate remains')
        return remaining[0], 'remaining_gap'

    if (step + 1) % _EXPLORE_PERIOD == 0:
        a, b, d, _ = max(mids, key=lambda v: (v[1] - v[0], -v[0]))
        return d, 'explore_largest_gap'

    def priority(item: tuple[int, int, int, int]) -> tuple[float, ...]:
        a, b, d, tier = item
        width = b - a
        if tier == 0:
            left_candidate = a if seen[a].feasible else b
            return (0, left_candidate, -width, d)
        if tier == 1:
            return (1, a, -width, d)
        violation = min(seen[a].worst_ber, seen[b].worst_ber)
        return (2, violation, -width, a)

    a, b, d, tier = min(mids, key=priority)
    return d, ('refine_feasibility_transition' if tier == 0 else
               'refine_feasible_region' if tier == 1 else 'probe_failed_region')


def select_step(evaluate: Callable[[int], Mapping[str, object]]) -> SearchOutcome:
    """Determine d1 without user tuning; callback supplies real BER/PSNR.

    Each unique d1 evaluation is cached. Eligibility requires confirmed zero
    clean errors and zero worst BER at d1=720. The best feasible PSNR remains
    non-decreasing throughout the trace, and no untested candidate is returned.
    """
    seen: dict[int, Measurement] = {}
    reasons: list[str] = []

    def measure(d1: int, reason: str) -> None:
        if d1 in seen:
            raise AssertionError('Duplicate expensive evaluation')
        row = _measurement(d1, evaluate(d1))
        seen[d1] = row
        reasons.append(reason)

    measure(_ANCHOR, 'eligibility_anchor')
    if not seen[_ANCHOR].feasible:
        return SearchOutcome('image_not_eligible', None, None,
                             tuple(seen.values()), tuple(reasons))

    for d in _PROBES:
        if len(seen) >= _BUDGET:
            break
        measure(d, 'geometric_initialization')

    while len(seen) < _BUDGET and len(seen) < _ANCHOR:
        d, reason = _next_candidate(seen, len(seen) - len(_PROBES) - 1)
        measure(d, reason)

    feasible = (m for m in seen.values() if m.feasible)
    best = min(feasible, key=lambda m: (-m.psnr_db, m.d1))
    return SearchOutcome('feasible', best.d1, best.psnr_db,
                         tuple(seen.values()), tuple(reasons))
