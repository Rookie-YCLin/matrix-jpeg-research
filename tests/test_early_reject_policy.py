"""Pure-python synthetic tests; these do not establish JPEG performance."""
import pytest

from experiments.early_reject_policy import quality_screen, all_qfs_verified_zero
from experiments.auto_zero_ber import select_step

QFS = (5, 10, 15, 20, 30, 50, 70, 90, 95)


def test_reject_first_failed_quality_without_extra_attacks():
    calls = []
    observed = quality_screen(
        QFS, 0, lambda q: (calls.append(q), 1 if q == 5 else 0)[1])
    assert observed == (5,)
    assert calls == [5]
    assert not all_qfs_verified_zero(QFS, observed, 0, (1,))


def test_failure_on_middle_qf_stops_at_exact_point():
    calls = []
    measured = quality_screen(
        QFS, 0, lambda q: (calls.append(q), 2 if q == 30 else 0)[1])
    assert measured == (5, 10, 15, 20, 30)
    assert calls == list(measured)
    assert not all_qfs_verified_zero(QFS, measured, 0, (0, 0, 0, 0, 2))


def test_complete_verification_needs_all_qfs_zero():
    measured = quality_screen(QFS, 0, lambda q: 0)
    assert measured == QFS
    assert all_qfs_verified_zero(QFS, measured, 0, (0,) * len(QFS))
    assert not all_qfs_verified_zero(QFS, measured[:-1], 0, (0,) * 8)
    assert not all_qfs_verified_zero(QFS, measured, 1, (0,) * 9)


def test_clean_failure_rejects_after_one_jpeg_and_no_false_success():
    calls = []
    measured = quality_screen(QFS, 3, lambda q: (calls.append(q), 0)[1])
    assert measured == (5,)
    assert not all_qfs_verified_zero(QFS, measured, 3, (0,))
    assert calls == [5]


def test_malformed_qf_or_error_count_rejected():
    for qualities in ((), (5, 5), (0, 5), (5, 101), (5.5,)):
        with pytest.raises(ValueError):
            quality_screen(qualities, 0, lambda q: 0)
    with pytest.raises(ValueError):
        quality_screen(QFS, -1, lambda q: 0)
    with pytest.raises(ValueError):
        quality_screen(QFS, 0, lambda q: -1)
    with pytest.raises(ValueError):
        quality_screen(QFS, 0, lambda q: float('nan'))


def test_partial_feedback_has_same_v2_candidate_order_as_full_feedback():
    # The current V2 selector uses feasibility + PNG PSNR for selection,
    # not full BER values. A rejected candidate's first nonzero BER is enough.
    def clean(d):
        return 0

    def qf_errors(d, q):
        if d >= 160 or 96 <= d <= 107:
            return 0
        return 1 if q == 5 else 0

    def full(d):
        errors = [qf_errors(d, q) for q in QFS]
        return {
            'worst_ber': max(errors) / 32,
            'clean_errors': clean(d),
            'png_psnr_db': 50 - d / 20,
        }

    def early(d):
        rows = []
        measured = quality_screen(
            QFS, clean(d), lambda q: (rows.append(qf_errors(d, q)), rows[-1])[1])
        assert len(measured) == len(rows)
        return {
            'worst_ber': max(rows) / 32,
            'clean_errors': clean(d),
            'png_psnr_db': 50 - d / 20,
        }

    assert select_step(full) == select_step(early)
