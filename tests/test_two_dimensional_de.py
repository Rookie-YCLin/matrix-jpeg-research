"""Fast synthetic contract tests; real JPEG evaluation is a separate experiment."""
from research.two_dimensional_de import Measurement, optimize_two_steps


def test_two_dimensional_de_reuses_exact_pair_measurements():
    calls = []
    def evaluator(d1, d2, qfs):
        calls.append((d1, d2))
        assert isinstance(d1, int) and isinstance(d2, int)
        assert 36 <= d1 <= 40
        assert 18 <= d2 <= 22
        # All pairs feasible: objective has a unique known optimum.
        return Measurement(
            psnr=40.0 - (d1 - 38) ** 2 - (d2 - 20) ** 2,
            clean_ber=0.0,
            jpeg_ber=tuple(0.0 for _ in qfs),
        )

    result = optimize_two_steps(
        evaluator, d1_bounds=(36, 40), d2_bounds=(18, 22),
        seed=7, popsize=8, maxiter=25,
    )
    assert result.feasible
    assert (result.d1, result.d2) == (38, 20)
    assert len(calls) == len(set(calls)) == result.unique_evaluations


def test_rejects_partial_jpeg_evaluation():
    def evaluator(d1, d2, qfs):
        return Measurement(30.0, 0.0, (0.0,))
    try:
        optimize_two_steps(evaluator, d1_bounds=(36, 37),
                           d2_bounds=(19, 20), maxiter=0)
    except ValueError as exc:
        assert "EVERY" in str(exc)
    else:
        raise AssertionError("Incomplete QF verification was accepted")
