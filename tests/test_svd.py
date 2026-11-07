import numpy as np
import pytest

from svd import decompose, reconstruct, validate


@pytest.mark.parametrize("matrix", [
    np.array([[0, 4, 0], [3, 0, 0]], dtype=np.float64),
    np.array([[0, 4], [3, 0], [0, 0]], dtype=np.float64),
])
def test_rectangular_rank_one_sum(matrix):
    factors = decompose(matrix)
    u, s, vh = factors
    np.testing.assert_allclose(s, [4, 3])
    for k in range(3):
        approximation = reconstruct(factors, k)
        terms = sum((s[i] * np.outer(u[:, i], vh[i]) for i in range(k)),
                    np.zeros_like(matrix))
        np.testing.assert_allclose(approximation, terms, atol=1e-12)
        assert np.linalg.matrix_rank(approximation) == k
        assert approximation.dtype == np.float64
    rows = validate(matrix, factors, [1])
    assert [row["frobenius_squared"] for row in rows] == pytest.approx([25, 9, 0])


def test_zero_matrix():
    matrix = np.zeros((3, 4))
    rows = validate(matrix, decompose(matrix), [1, 2])
    assert all(row["frobenius_squared"] == row["tail_squared"] == 0 for row in rows)


@pytest.mark.parametrize("rank", [-1, 3])
def test_out_of_range_rank(rank):
    with pytest.raises(ValueError, match="k must be"):
        reconstruct(decompose(np.eye(2)), rank)


def test_validation_rejects_inconsistent_factors():
    matrix = np.diag([4.0, 3.0])
    u, s, vh = decompose(matrix)
    with pytest.raises(AssertionError, match="Frobenius tail identity"):
        validate(matrix, (u, s * 2, vh), [1])
