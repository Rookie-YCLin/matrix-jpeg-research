"""Mathematical, adversarial and certificate tests for spectral QIM.

No artificial JPEG BER model is ever offered as evidence of real performance.
The synthetic oracle is ONLY for verifying the ranking/certificate theorem.
"""
import numpy as np
import pytest

from experiments.spectral_certificate_qim import (
    DOMAIN, D2, QFS, select_certified, spectral_energies,
)


def fake_observation(d, *, valid):
    errors = [0] * len(QFS) if valid else [1]
    checked = QFS if valid else QFS[:1]
    return {
        "png_psnr_db": 27.0 + (d % 4) * 0.1,
        "clean_errors": 0,
        "worst_ber": 0.0 if valid else 1 / 32,
        "jpeg_attacks": len(checked),
        "tested_qfs": ",".join(map(str, checked)),
        "qf_error_counts": ",".join(map(str, errors)),
        "full_qf_verification": valid,
    }


def fake_profile(preferred=96):
    return {d: float((d-preferred)**2) for d in DOMAIN}


def test_exact_squared_singular_value_distortion_matches_frobenius_norm():
    rng = np.random.default_rng(23)
    a = rng.normal(size=(4, 4))
    b = rng.normal(size=(4, 4))
    u, s, vt = np.linalg.svd(a)
    u2, s2, vt2 = np.linalg.svd(b)
    original = (u * s[None, :]) @ vt
    original2 = (u2 * s2[None, :]) @ vt2
    for d in (1, 17, 36, 96, 720):
        observed = spectral_energies(
            np.array([s[0], s2[0]]),
            np.array([s[1], s2[1]]),
            np.array([0, 1]),
            (d,),
        )[d]
        targets = [
            np.array([(np.floor(s[0]/d) + .25)*d,
                      (np.floor(s[1]/D2) + .25)*D2,
                      s[2], s[3]]),
            np.array([(np.floor(s2[0]/d) + .75)*d,
                      (np.floor(s2[1]/D2) + .75)*D2,
                      s2[2], s2[3]]),
        ]
        rebuilt = (u * targets[0][None, :]) @ vt
        rebuilt2 = (u2 * targets[1][None, :]) @ vt2
        frobenius = (np.linalg.norm(rebuilt-original, "fro")**2
                     + np.linalg.norm(rebuilt2-original2, "fro")**2)
        assert observed == pytest.approx(frobenius, rel=1e-11, abs=1e-11)


def test_chunk_size_does_not_change_720_step_profile():
    sigma0 = np.array([12.25, 101.3, 240.1, 9.5])
    sigma1 = np.array([2.7, 8.9, 30.1, 4.5])
    bits = np.array([0, 1, 0, 1])
    a = spectral_energies(sigma0, sigma1, bits, chunk=1)
    b = spectral_energies(sigma0, sigma1, bits, chunk=63)
    assert a.keys() == b.keys()
    assert all(a[d] == pytest.approx(b[d], rel=1e-12) for d in DOMAIN)


def test_global_minimum_certificate_checks_all_strictly_better_candidates():
    scores = fake_profile()
    tested = []
    # d1=96 has the best SVD distortion but fails an actual constraint.
    # d1=97 is the next-lowest with a valid full-nine-QF certificate.
    result = select_certified(
        scores, lambda d: (tested.append(d), fake_observation(d,valid=d==97))[1]
    )
    assert tested == [96, 95, 97]
    assert result.status == "certified_spectral_global_optimum"
    assert result.certified
    assert result.best_d1 == 97
    assert result.best_transform_energy == scores[97]
    assert set(tested[:-1]) == {
        d for d in DOMAIN
        if (scores[d], d) < (scores[97], 97)
    }


def test_hidden_island_is_discoverable_with_no_monotonic_ber_assumption():
    scores = fake_profile(preferred=149)
    successful = {90, 148, 177}
    result = select_certified(scores, lambda d: fake_observation(
        d, valid=d in successful
    ))
    assert result.best_d1 == 148
    assert result.certified
    assert all(d not in successful for d in result.attempted_steps[:-1])


def test_budget_exhaustion_does_not_claim_global_optimality():
    scores = fake_profile()
    result = select_certified(
        scores, lambda d: fake_observation(d, valid=False),
        max_evaluations=20,
    )
    assert result.status == "evaluation_budget_exhausted"
    assert result.best_d1 is None
    assert not result.certified
    assert result.evaluations == 20


def test_infeasible_everywhere_requires_full_720_rejections():
    result = select_certified(
        fake_profile(), lambda d: fake_observation(d, valid=False),
    )
    assert result.status == "certified_no_feasible_in_domain"
    assert result.evaluations == 720
    assert result.certified


def test_no_unknown_qf_may_be_accepted_as_full_certificate():
    scores = fake_profile()
    def malicious(d):
        values = fake_observation(d, valid=False)
        values["worst_ber"] = 0.0
        values["qf_error_counts"] = "0"
        values["full_qf_verification"] = True
        return values
    with pytest.raises(ValueError):
        select_certified(scores, malicious)


@pytest.mark.parametrize("profile", [
    {1: 0.0},
    {d: -1.0 for d in DOMAIN},
    {d: float("nan") for d in DOMAIN},
    {d: float("inf") for d in DOMAIN},
])
def test_invalid_profiles_fail_closed(profile):
    with pytest.raises(ValueError):
        select_certified(profile, lambda d: fake_observation(d, valid=True))


@pytest.mark.parametrize("max_evaluations", [0, True, 721, 3.5])
def test_invalid_budget_fails_closed(max_evaluations):
    with pytest.raises(ValueError):
        select_certified(
            fake_profile(), lambda d: fake_observation(d, valid=True),
            max_evaluations=max_evaluations,
        )


def test_invalid_spectral_inputs_fail_closed():
    with pytest.raises(ValueError):
        spectral_energies(
            np.array([1.0, 2.0]), np.array([3.0]),
            np.array([1.0, 0.0]),
        )
    with pytest.raises(ValueError):
        spectral_energies(
            np.array([1.0]), np.array([0.3]), np.array([2]),
        )
