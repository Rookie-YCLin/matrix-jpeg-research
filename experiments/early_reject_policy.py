"""Provably safe screening for all-QF-zero-BER *feasibility*.

A tested quality factor with a bit error is a witness that the candidate
fails the hard all-QF constraint. There is no need to perform the remaining
JPEG attacks to *reject* that candidate. This says nothing about BER at
the untested QFs, which must remain unreported.

The selection objective and selector are NOT changed.
"""
from __future__ import annotations

from typing import Callable, Sequence


def quality_screen(
    qfs: Sequence[int],
    clean_errors: int,
    measure_errors: Callable[[int], int],
) -> tuple[int, ...]:
    """Return exactly the QFs actually evaluated, stopping at first violation.

    At least one QF is measured, including when clean extraction already fails,
    so downstream worst_ber is always a maximum of *observed* BER values.
    A clean-extraction error is itself disqualifying and needs no further JPEG.
    """
    qfs = tuple(qfs)
    if not qfs or len(set(qfs)) != len(qfs) or any(
        type(qf) is not int or not 1 <= qf <= 100 for qf in qfs
    ):
        raise ValueError("QFs must be unique integer qualities in 1..100")
    if type(clean_errors) is not int or clean_errors < 0:
        raise ValueError("clean_errors must be a nonnegative integer")
    measured: list[int] = []
    for qf in qfs:
        errors = measure_errors(qf)
        if type(errors) is not int or errors < 0:
            raise ValueError("JPEG extraction must report nonnegative integer errors")
        measured.append(qf)
        if clean_errors != 0 or errors != 0:
            break
    return tuple(measured)


def all_qfs_verified_zero(
    requested_qfs: Sequence[int],
    measured_qfs: Sequence[int],
    clean_errors: int,
    error_counts: Sequence[int],
) -> bool:
    """Never certify a candidate from partial measurements."""
    return (
        clean_errors == 0
        and tuple(requested_qfs) == tuple(measured_qfs)
        and len(error_counts) == len(requested_qfs)
        and all(count == 0 for count in error_counts)
    )
