"""Deterministic policy tests; synthetic measurements are NOT JPEG evidence."""
import pytest

from experiments.auto_zero_ber import select_step


def example(d):
    return {
        'worst_ber': 0.0 if d >= 100 or 40 <= d <= 43 else .125,
        'clean_errors': 0,
        'png_psnr_db': 50 - d / 20,
    }


def test_automatic_candidates_unique_and_budget():
    queried = []
    result = select_step(lambda d: (queried.append(d), example(d))[1])
    assert result.status == 'feasible'
    assert result.evaluations == 36
    assert len(queried) == len(set(queried))
    assert result.best_d1 in queried
    assert result.best_psnr_db == max(
        m.psnr_db for m in result.measurements if m.feasible
    )
    assert result.measurements[0].d1 == 720
    assert 'explore_largest_gap' in result.reasons


def test_unqualified_image_stops_at_eligibility():
    result = select_step(
        lambda d: {'worst_ber': .1, 'clean_errors': 0, 'png_psnr_db': 20}
    )
    assert result.status == 'image_not_eligible'
    assert result.evaluations == 1
    assert result.best_d1 is None


def test_clean_extraction_is_hard_constraint():
    result = select_step(
        lambda d: {
            'worst_ber': 0.,
            'clean_errors': int(d != 720),
            'png_psnr_db': 100 - d / 10,
        }
    )
    assert result.best_d1 == 720


def test_reproducible_and_history_only():
    assert select_step(example) == select_step(example)


def test_invalid_measurements_rejected():
    with pytest.raises(ValueError):
        select_step(
            lambda d: {'worst_ber': float('nan'), 'clean_errors': 0, 'png_psnr_db': 20}
        )
    with pytest.raises(ValueError):
        select_step(
            lambda d: {'worst_ber': 0, 'clean_errors': -1, 'png_psnr_db': 20}
        )


def test_disconnected_feasible_island_and_anchor_guarantee():
    def islands(d):
        return {
            'worst_ber': 0.0 if (98 <= d <= 103 or d >= 400) else .25,
            'clean_errors': 0,
            'png_psnr_db': 60 - d / 20,
        }

    outcome = select_step(islands)
    assert outcome.best_d1 is not None
    assert islands(outcome.best_d1)['worst_ber'] == 0.
    assert outcome.best_d1 in {m.d1 for m in outcome.measurements}
    assert outcome.best_psnr_db >= islands(720)['png_psnr_db']
