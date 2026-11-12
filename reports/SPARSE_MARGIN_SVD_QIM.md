# Sparse-margin SVD-QIM: a BER--PSNR compromise

This candidate concentrates a large first-singular-value QIM period in a deterministic sparse subset of blocks. It is a new blind embedding/extraction algorithm, not a post-processing correction and not a claim of global optimality.

## Algorithm

The image pipeline, original image, 32-bit payload, keys, DWT, DCT, block shuffle and JPEG setup are unchanged. For a block index `i` and watermark length `L=32`, select it exactly when

```text
(i // L) mod 32 = 0.
```

The selected block embeds its repeated payload bit into its first singular value with the upstream QIM rule and `d1=720`. It leaves the second singular value unchanged; `d2=20` remains the configured upstream parameter. An unselected block is copied unchanged. At blind extraction the same index rule selects the votes; the decoder takes the mean of those votes per payload coordinate and then runs the existing one-dimensional K-means. It receives neither JPEG QF, original image, nor expected bits.

Each payload coordinate therefore has the same count of selected replicas in every channel. In this image, 396 repeated cycles give 13 selected copies per coordinate per channel, or 39 votes per bit.

For a selected SVD block with fixed singular vectors, the perturbation obeys

`||A' - A||_F^2 = sum_i (sigma'_i - sigma_i)^2`.

Unselected blocks contribute zero to this sum. Sparsity therefore lowers the accumulated local spectral modification compared with applying the same `d1=720` everywhere. The local singular-value inequality `|sigma_i(A+E)-sigma_i(A)| <= ||E||_2` explains why a larger QIM margin can survive larger perturbations, but neither expression proves RGB PSNR or JPEG BER after the nonlinear image pipeline. Those are empirical results below.

## Results

| Scheme | PNG PSNR | QF5 BER | QF10 BER | QF15 BER | QF20 BER |
|---|---:|---:|---:|---:|---:|
| G6 all-block `(90,20)` | 31.801 dB | 32/32 | 0/32 | 0/32 | 0/32 |
| All-block margin `(720,20)` | 15.564 dB | 0/32 | 0/32 | 0/32 | 0/32 |
| Sparse-margin, selected `d1=720` | 31.083 dB | 0/32 | 0/32 | 0/32 | 0/32 |

The sparse candidate has QF5 PSNR 23.952 dB, versus G6 24.143 dB, and QF15 PSNR 27.304 dB, versus G6 27.554 dB. Thus it removes the observed QF5 failure with a 0.718 dB PNG PSNR reduction relative to G6, while avoiding the severe all-block margin distortion. It does not meet a 35 dB PNG target, so it remains a trade-off candidate rather than a claim of imperceptibility.

The complete existing grid QF=5,10,...,95 is 0/32 at every point; PNG is 0/32. This only establishes the result for the one specified image, payload, keys, fixed Pillow encoder and sampled QFs. QF1--4 and QF6--9 were not measured.

## Evidence and reproduction

- [Pre-registered design](../docs/SPARSE_MARGIN_PLAN.md)
- [Low-QF results and manifest](../outputs/sparse-margin720/results.csv)
- [Complete QF grid and manifest](../outputs/sparse-margin720-validation/results.csv)
- [Implementation](../experiments/paper_low_qf.py)

```text
python -m experiments.paper_low_qf --output-dir outputs/sparse-margin-local --variants sparse_margin720 --qualities 5 10 15 20 25 30 35 40 45 50 55 60 65 70 75 80 85 90 95
python -m pytest -q
```

The local verification suite has 30 passing tests, including the sparse schedule's equal-replica-count check.
