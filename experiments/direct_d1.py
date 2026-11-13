"""Discrete 1-D DIRECTGO-inspired search for the existing nine-QF zero-BER study.

Based on DIRECTGO's dX_DTC_GL.m and Stripinis & Paulavicius (2026).
This is NOT a Python port of X-DTC-GL: it adapts interval trisection,
global/local region selection, and a guarded three-point quadratic surrogate
to integer d1 with discontinuous, hard BER constraints. The MATLAB algorithm
assumes continuous box-constrained scalar objectives, and its SQP hill
climber is deliberately NOT copied into the discontinuous integer problem.

No tuning arguments are exposed to the end user. Exactly the same 36 unique
real evaluation budget and verified d1=720 eligibility rule as V2 are used.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Callable, Mapping

from experiments.auto_zero_ber import Measurement, SearchOutcome, _measurement

ANCHOR = 720
BUDGET = 36
LOW = 1


@dataclass(frozen=True)
class Cell:
    lo: int
    hi: int
    center: int

    @property
    def span(self) -> int:
        return self.hi - self.lo + 1


def _score(m: Measurement) -> float:
    """Ordering only; zero-BER and clean extraction remain hard constraints."""
    return -m.psnr_db if m.feasible else 1000.0 + m.worst_ber + m.clean_errors


def _children(cell: Cell) -> list[Cell]:
    """Ternary integer partition; bisect the final 2-point cells."""
    n = cell.span
    if n < 2:
        return []
    if n == 2:
        parts = [(cell.lo, cell.lo), (cell.hi, cell.hi)]
    else:
        flank = n // 3
        a = cell.lo + flank
        b = cell.hi - flank
        parts = [(cell.lo, a - 1), (a, b), (b + 1, cell.hi)]
    children = [Cell(a, b, (a + b) // 2) for a, b in parts]
    if not any(child.center == cell.center for child in children):
        raise AssertionError('A split must retain the old center sample')
    return children


def _pareto(cells: list[Cell], seen: Mapping[int, Measurement]) -> list[Cell]:
    """Nondominated: larger unsearched span and smaller observed score."""
    out = []
    for cell in cells:
        s = _score(seen[cell.center])
        if not any(
            (other.span >= cell.span and _score(seen[other.center]) <= s)
            and (other.span > cell.span or _score(seen[other.center]) < s)
            for other in cells if other is not cell
        ):
            out.append(cell)
    return out


def _boundary_cell(cells: list[Cell], seen: Mapping[int, Measurement]) -> Cell | None:
    """Refine measured feasible/infeasible transitions, without monotonicity."""
    ordered = sorted(seen)
    boundaries = [
        (a, b) for a, b in zip(ordered, ordered[1:])
        if b-a > 1 and seen[a].feasible != seen[b].feasible
    ]
    if not boundaries:
        return None
    options = []
    for a, b in boundaries:
        midpoint = (a+b)/2
        for cell in cells:
            if cell.span < 2 or cell.hi < a or cell.lo > b:
                continue
            options.append((b-a, -abs(cell.center-midpoint), cell.span,
                            -cell.lo, cell))
    return max(options, key=lambda v: v[:-1])[-1] if options else None


def _surrogate_probe(seen: Mapping[int, Measurement]) -> int | None:
    """Optional convex 3-point interpolant; never used to certify feasibility.

    Only use triples already verified feasible. Model predictions are merely
    candidate proposals, not substitutions for JPEG evaluations.
    """
    candidates = []
    best_score = min(_score(m) for m in seen.values() if m.feasible)
    # Do not bridge an infeasible observed point between feasible samples.
    all_points = sorted(seen)
    for i in range(len(all_points)-2):
        x0, x1, x2 = all_points[i:i+3]
        if not all(seen[x].feasible for x in (x0,x1,x2)):
            continue
        y0,y1,y2 = (_score(seen[x]) for x in (x0,x1,x2))
        s01 = (y1-y0)/(x1-x0)
        s12 = (y2-y1)/(x2-x1)
        a = (s12-s01)/(x2-x0)
        if not isfinite(a) or a <= 1e-12:
            continue
        # f(x)=a*(x-x1)^2 + b*(x-x1) + y1
        b = s01 + a*(x1-x0)
        predicted_x = x1-b/(2*a)
        x = int(round(predicted_x))
        if not (x0 < x < x2) or x in seen:
            continue
        predicted = y1 + b*(x-x1) + a*(x-x1)**2
        if predicted < best_score - 1e-4:
            candidates.append((predicted, x))
    return min(candidates)[1] if candidates else None


def _select_cell(cells: list[Cell], seen: Mapping[int, Measurement],
                 split_count: int) -> tuple[Cell, str]:
    available = [c for c in cells if c.span >= 2]
    if not available:
        raise RuntimeError('No refinable intervals')
    phase = split_count % 5
    if phase in (1, 3):
        boundary = _boundary_cell(available, seen)
        if boundary is not None:
            return boundary, 'refine_feasibility_boundary'
    pareto = _pareto(available, seen)
    if phase == 4:
        return max(available, key=lambda c: (c.span, -_score(seen[c.center]), -c.lo)), 'global_largest_interval'
    return min(pareto, key=lambda c: (_score(seen[c.center]), -c.span, c.lo)), 'direct_pareto_local'


def select_direct_step(evaluate: Callable[[int], Mapping[str, object]]) -> SearchOutcome:
    """Autonomous, deterministic, history-only real-JPEG callback interface."""
    seen: dict[int, Measurement] = {}
    reasons: list[str] = []

    def measure(d: int, reason: str) -> None:
        if d in seen:
            raise AssertionError(f'Duplicate expensive d1={d}')
        seen[d] = _measurement(d, evaluate(d))
        reasons.append(reason)

    measure(ANCHOR, 'eligibility_anchor')
    if not seen[ANCHOR].feasible:
        return SearchOutcome('image_not_eligible', None, None,
                             tuple(seen.values()), tuple(reasons))

    root = Cell(LOW, ANCHOR, (LOW+ANCHOR)//2)
    measure(root.center, 'direct_center_initialization')
    cells = [root]
    splits = 0

    while len(seen) < BUDGET:
        # The surrogate is deliberately conservative because BER is not smooth.
        if splits > 0 and splits % 5 == 0:
            probe = _surrogate_probe(seen)
            if probe is not None:
                measure(probe, 'guarded_quadratic_surrogate')
                continue
        cell, reason = _select_cell(cells, seen, splits)
        cells.remove(cell)
        children = _children(cell)
        for child in children:
            if child.center not in seen and len(seen) < BUDGET:
                measure(child.center, reason)
        cells.extend(children)
        splits += 1

    best = min((m for m in seen.values() if m.feasible),
               key=lambda m: (-m.psnr_db, m.d1))
    return SearchOutcome('feasible', best.d1, best.psnr_db,
                         tuple(seen.values()), tuple(reasons))
