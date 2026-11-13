"""Two-parameter integer DE search for the guofei SVD-QIM watermark.

The evaluator must embed with both d1 and d2 in normal (non-fast) mode,
measure PNG PSNR, and decode clean plus every requested JPEG quality.
No result is treated as feasible until all ten checks are observed.
This module deliberately does not modify the watermark implementation.
"""
from dataclasses import dataclass
from functools import lru_cache
from typing import Callable, Sequence

import numpy as np
from scipy.optimize import NonlinearConstraint, differential_evolution

QFS = (5, 10, 15, 20, 30, 50, 70, 90, 95)


@dataclass(frozen=True)
class Measurement:
    psnr: float
    clean_ber: float
    jpeg_ber: tuple[float, ...]


@dataclass(frozen=True)
class SearchResult:
    d1: int
    d2: int
    psnr: float
    feasible: bool
    unique_evaluations: int
    solver_evaluations: int
    seed: int


def optimize_two_steps(
    evaluator: Callable[[int, int, Sequence[int]], Measurement],
    *,
    d1_bounds: tuple[int, int] = (36, 720),
    d2_bounds: tuple[int, int] = (1, 120),
    qfs: Sequence[int] = QFS,
    seed: int = 42,
    popsize: int = 15,
    maxiter: int = 30,
) -> SearchResult:
    """Run SciPy's integer DE with exact zero-BER feasibility.

    The d2 interval is a pilot *assumption*, not an upstream specification.
    Every distinct pair is evaluated once (memoized). SciPy's Lampinen-style
    constraint handling ranks feasible solutions ahead of infeasible ones.
    """
    if not qfs or len(set(qfs)) != len(qfs):
        raise ValueError("qfs must be nonempty and distinct")
    if any(lo > hi or lo < 1 for lo, hi in (d1_bounds, d2_bounds)):
        raise ValueError("bounds must contain positive integers")
    if popsize < 4 or maxiter < 0:
        raise ValueError("invalid DE budget")

    @lru_cache(maxsize=None)
    def measure(d1: int, d2: int) -> Measurement:
        m = evaluator(d1, d2, qfs)
        if len(m.jpeg_ber) != len(qfs):
            raise ValueError("Evaluator must check EVERY requested JPEG QF")
        vals = (m.psnr, m.clean_ber, *m.jpeg_ber)
        if not all(np.isfinite(v) for v in vals):
            raise ValueError("Non-finite PSNR or BER")
        if any(not 0 <= v <= 1 for v in vals[1:]):
            raise ValueError("BER must lie in [0, 1]")
        return m

    def pair(x):
        return int(x[0]), int(x[1])

    def objective(x):
        m = measure(*pair(x))
        return -m.psnr

    def violations(x):
        m = measure(*pair(x))
        return np.asarray((m.clean_ber, *m.jpeg_ber), dtype=float)

    constraint = NonlinearConstraint(violations, 0.0, 0.0)
    result = differential_evolution(
        objective,
        bounds=[d1_bounds, d2_bounds],
        constraints=(constraint,),
        integrality=[True, True],
        strategy="rand1bin",
        popsize=popsize,
        maxiter=maxiter,
        mutation=(0.5, 1.0),
        recombination=0.7,
        polish=False,
        rng=np.random.default_rng(seed),
        updating="immediate",
    )

    return _finalize(result, measure, seed)


def _finalize(result, measure, seed):
    d1, d2 = (int(v) for v in result.x)
    m = measure(d1, d2)
    return SearchResult(
        d1=d1, d2=d2, psnr=m.psnr,
        feasible=(m.clean_ber == 0 and all(v == 0 for v in m.jpeg_ber)),
        unique_evaluations=measure.cache_info().currsize,
        solver_evaluations=int(result.nfev), seed=seed,
    )
