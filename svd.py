"""Float64 rank-k reconstruction and numerical checks."""
import numpy as np

RTOL = 1e-8
ATOL = 1e-12


def decompose(matrix):
    matrix = np.asarray(matrix, dtype=np.float64)
    if matrix.ndim != 2 or not matrix.size or not np.isfinite(matrix).all():
        raise ValueError("SVD requires a finite, nonempty 2-D matrix")
    return np.linalg.svd(matrix, full_matrices=False)


def reconstruct(factors, k):
    u, s, vh = factors
    if not 0 <= k <= s.size:
        raise ValueError(f"k must be between 0 and {s.size}")
    return (u[:, :k] * s[:k]) @ vh[:k, :]


def validate(matrix, factors, ranks):
    u, s, vh = factors
    p = min(matrix.shape)
    if (u.shape, s.shape, vh.shape) != ((matrix.shape[0], p), (p,), (p, matrix.shape[1])):
        raise ValueError("Unexpected reduced SVD dimensions")
    if not np.isfinite(s).all() or np.any(s < 0) or np.any(np.diff(s) > 0):
        raise ValueError("Singular values must be finite, nonnegative and descending")
    identity = np.eye(p)
    np.testing.assert_allclose(u.T @ u, identity, rtol=0, atol=ATOL)
    np.testing.assert_allclose(vh @ vh.T, identity, rtol=0, atol=ATOL)

    energy = float(np.sum(matrix * matrix))
    scale = energy or 1.0
    rows = []
    previous = np.inf
    for k in sorted({0, *ranks, p}):
        approximation = reconstruct(factors, k)
        if approximation.shape != matrix.shape:
            raise ValueError(f"Wrong reconstruction shape at k={k}")
        residual = float(np.linalg.norm(matrix - approximation, "fro") ** 2)
        tail = float(np.sum(s[k:] ** 2))
        relative = residual / scale
        np.testing.assert_allclose(relative, tail / scale, rtol=RTOL, atol=ATOL,
                                   err_msg=f"Frobenius tail identity failed at k={k}")
        if relative > previous + ATOL:
            raise ValueError(f"Normalized error increased at k={k}: {previous} -> {relative}")
        if energy == 0 and (residual != 0 or tail != 0):
            raise ValueError(f"Expected exact zero error at k={k}")
        rows.append({
            "k": k, "frobenius_squared": residual, "tail_squared": tail,
            "relative_squared": relative, "relative_tail_squared": tail / scale,
        })
        previous = relative
    return rows
