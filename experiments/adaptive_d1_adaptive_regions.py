"""Budgeted integer d1 optimizer: competing local basins and periodic exploration.

The objective callback is the only source of BER/PSNR information. Every
candidate is unique and consumes exactly one expensive evaluation.
"""
from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class SearchResult:
    best_d1: int
    best_objective: float
    trace: tuple[tuple[int, float], ...]


def optimize(objective: Callable[[int], float], *, low: int = 1,
             high: int = 150, budget: int = 24, coarse: int = 8,
             regions: int = 3, separation: int = 10,
             explore_every: int = 6) -> SearchResult:
    if not (1 <= coarse <= budget <= high - low + 1):
        raise ValueError("Invalid coarse, budget or domain")
    if regions < 1 or separation < 0 or explore_every < 0:
        raise ValueError("Invalid search parameters")
    seen: dict[int, float] = {}
    trace: list[tuple[int, float]] = []

    def evaluate(x: int) -> None:
        if x in seen:
            raise AssertionError("Duplicate objective evaluation")
        value = float(objective(x))
        if value != value:
            raise ValueError("NaN objective")
        seen[x] = value
        trace.append((x, value))

    width = high - low + 1
    for i in range(coarse):
        d = min(high, low + int((i + 0.5) * width / coarse))
        if d in seen:
            d = next(x for x in range(low, high + 1) if x not in seen)
        evaluate(d)

    while len(seen) < budget:
        available = [x for x in range(low, high + 1) if x not in seen]
        steps = len(seen) - coarse
        if explore_every and steps and steps % explore_every == 0:
            candidate = max(available, key=lambda x: (min(abs(x-z) for z in seen), -x))
        else:
            centers: list[int] = []
            for d in sorted(seen, key=lambda x: (seen[x], x)):
                if all(abs(d-c) > separation for c in centers):
                    centers.append(d)
                if len(centers) >= regions:
                    break
            spread = max(seen.values()) - min(seen.values())
            scale = max(spread, 1e-9) * 0.12
            choices = []
            for center in centers:
                local = [x for x in seen if abs(x-center) <= separation]
                nearby = min(available, key=lambda x: (abs(x-center), x))
                priority = seen[center] + scale * len(local) / (1+coarse)
                choices.append((priority, nearby, center))
            candidate = min(choices)[1]
        evaluate(candidate)

    best = min(seen, key=lambda d: (seen[d], d))
    return SearchResult(best, seen[best], tuple(trace))
