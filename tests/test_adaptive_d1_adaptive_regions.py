"""Tests for competing-region integer search (no JPEG needed)."""
import pytest
from experiments.adaptive_d1_adaptive_regions import optimize


def test_unique_and_budget():
    queried = []
    result = optimize(lambda d: queried.append(d) or abs(d-33), budget=24)
    assert len(queried) == len(set(queried)) == 24
    assert result.best_objective == min(abs(d-33) for d in queried)
    assert result.best_d1 in queried


def test_disconnected_basins():
    def f(d):
        return min((d-27)**2/300, 0.2+(d-113)**2/300)
    result = optimize(f, budget=48)
    assert len(result.trace) == 48
    assert result.best_objective >= 0


def test_rejects_invalid():
    with pytest.raises(ValueError):
        optimize(lambda x: x, budget=3, coarse=8)
    with pytest.raises(ValueError):
        optimize(lambda x: float("nan"))
