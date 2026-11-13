"""Deterministic policy tests. Synthetic functions are NOT JPEG measurements."""
from experiments.direct_d1 import (
    ANCHOR, BUDGET, Cell, _children, _surrogate_probe, select_direct_step,
)
from experiments.auto_zero_ber import Measurement
import pytest


def fake(d):
    return {
        'worst_ber': 0 if d >= 140 or 97 <= d <= 107 else 0.5,
        'clean_errors': 0,
        'png_psnr_db': 50 - d / 20,
    }


def test_partition_centers_preserved_no_lost_indices():
    for size in range(2, 721):
        parent = Cell(1, size, (1 + size)//2)
        children = _children(parent)
        assert children[0].lo == 1
        assert children[-1].hi == size
        assert sum(c.span for c in children) == size
        assert all(a.hi+1 == b.lo for a, b in zip(children, children[1:]))
        assert parent.center in [c.center for c in children]


def test_search_budget_uniqueness_verified_incumbent():
    trace = []
    out = select_direct_step(lambda d: (trace.append(d), fake(d))[1])
    assert out.status == 'feasible'
    assert out.evaluations == BUDGET
    assert len(trace) == len(set(trace))
    assert trace[0] == ANCHOR
    assert out.best_d1 in trace
    assert fake(out.best_d1)['worst_ber'] == 0
    assert out.best_psnr_db == max(
        x.psnr_db for x in out.measurements if x.feasible
    )
    assert any('boundary' in r or 'global' in r for r in out.reasons)


def test_failed_anchor_is_not_misreported_as_infeasible_domain():
    out = select_direct_step(
        lambda d: {'worst_ber': 0.1, 'clean_errors': 0, 'png_psnr_db': 50})
    assert out.status == 'image_not_eligible'
    assert out.evaluations == 1
    assert out.best_d1 is None


def test_clean_error_is_hard_constraint():
    out = select_direct_step(lambda d: {
        'worst_ber': 0.,
        'clean_errors': int(d != 720),
        'png_psnr_db': 80 - d / 20,
    })
    assert out.best_d1 == ANCHOR


def test_determinism_without_lookahead():
    assert select_direct_step(fake) == select_direct_step(fake)


def test_invalid_values_rejected():
    with pytest.raises(ValueError):
        select_direct_step(lambda d: {
            'worst_ber': float('nan'), 'clean_errors': 0, 'png_psnr_db': 30
        })


def test_parabolic_hint_only_with_measured_feasible_triplet():
    seen = {
        d: Measurement(d, 0, 0, 50 - (d - 150)**2 / 100)
        for d in (100, 140, 200)
    }
    assert _surrogate_probe(seen) == 150
    seen[140] = Measurement(140, .25, 0, 49)
    assert _surrogate_probe(seen) is None


def test_nonmonotonic_islands_no_unmeasured_answer():
    def islands(d):
        return {
            'worst_ber': 0 if (95 <= d <= 105 or 160 <= d <= 180 or d >= 500) else .8,
            'clean_errors': 0,
            'png_psnr_db': 55 - d / 20,
        }
    out = select_direct_step(islands)
    assert out.best_d1 in [m.d1 for m in out.measurements]
    assert islands(out.best_d1)['worst_ber'] == 0
    assert out.best_psnr_db >= islands(720)['png_psnr_db']
