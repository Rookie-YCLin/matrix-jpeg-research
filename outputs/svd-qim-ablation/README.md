# SVD–QIM controlled ablation (2026-11-14)

[Successful GitHub Actions run](https://github.com/Rookie-YCLin/matrix-jpeg-research/actions/runs/43599575419)

## Design

Pinned guofei9987/blind_watermark commit `322c90dc02d45644692095b34d3a6b735b6edbd8`. One original `ori_img.jpeg`, 32-bit fixed payload `10110010111001000101101011010001` is **not** necessarily the original payload, so use the payload explicitly specified in `experiments/ori_qf_scan.py` instead. Same passwords, fixed 4:4:4 Pillow JPEG encoding, QFs 5,10,15,20,25,50,95 and no-attack PNG.

Six arms: common mode d1=36 and 90 with d2=0 or 20; fast mode d1=36 and 90 with d2=0. In fast mode d2 is ignored by the upstream implementation. Each arm uses the same original bit pattern and blind extraction.

K-means decisions were reproduced using the upstream `one_dim_kmeans` and correct watermark-key de-permutation; fixed threshold 0.5 was independently applied to the same decrypted mean confidence scores. The `oracle_polarity_errors=min(errors,32-errors)` column **uses ground truth for diagnostics** and is not a valid blind-recovery BER.

## Selected results

| Arm | QF | K-means errors | Threshold errors | Oracle polarity residual | PSNR dB |
|---|---|---:|---:|---:|---:|
| common_36_20 | PNG | 0/32 | 0/32 | 0/32 | 38.401 |
| common_36_20 | 5 | 12/32 | 16/32 | 12/32 | 24.737 |
| common_36_20 | 10 | 1/32 | 16/32 | 1/32 | 27.890 |
| common_36_20 | 15 | 32/32 | 16/32 | 0/32 | 29.225 |
| common_36_20 | 20 | 32/32 | 16/32 | 0/32 | 29.967 |
| common_36_0 | PNG | 0/32 | 0/32 | 0/32 | 39.886 |
| common_36_0 | 5 | 11/32 | 16/32 | 11/32 | 24.745 |
| common_36_0 | 10 | 1/32 | 16/32 | 1/32 | 27.918 |
| common_36_0 | 15 | 32/32 | 16/32 | 0/32 | 29.242 |
| common_36_0 | 20 | 32/32 | 16/32 | 0/32 | 29.991 |
| fast_36 | PNG | 0/32 | 0/32 | 0/32 | 39.891 |
| fast_36 | 5 | 11/32 | 16/32 | 11/32 | 24.744 |
| fast_36 | 10 | 1/32 | 16/32 | 1/32 | 27.921 |
| fast_36 | 15 | 32/32 | 16/32 | 0/32 | 29.238 |
| fast_36 | 20 | 32/32 | 16/32 | 0/32 | 29.995 |
| common_90_20 | PNG | 0/32 | 0/32 | 0/32 | 31.801 |
| common_90_20 | 5 | 32/32 | 16/32 | 0/32 | 24.143 |
| common_90_20 | 10 | 0/32 | 16/32 | 0/32 | 26.682 |
| common_90_20 | 15 | 0/32 | 0/32 | 0/32 | 27.554 |
| common_90_20 | 20 | 0/32 | 0/32 | 0/32 | 28.104 |
| common_90_0 | PNG | 0/32 | 0/32 | 0/32 | 32.058 |
| common_90_0 | 5 | 32/32 | 16/32 | 0/32 | 24.148 |
| common_90_0 | 10 | 0/32 | 16/32 | 0/32 | 26.718 |
| common_90_0 | 15 | 0/32 | 0/32 | 0/32 | 27.537 |
| common_90_0 | 20 | 0/32 | 0/32 | 0/32 | 28.194 |
| fast_90 | PNG | 0/32 | 0/32 | 0/32 | 32.062 |
| fast_90 | 5 | 32/32 | 16/32 | 0/32 | 24.142 |
| fast_90 | 10 | 0/32 | 16/32 | 0/32 | 26.717 |
| fast_90 | 15 | 0/32 | 0/32 | 0/32 | 27.515 |
| fast_90 | 20 | 0/32 | 0/32 | 0/32 | 28.201 |

## Findings

1. Removing d2 at d1=36 raises clean-image PSNR from about 38.401 to 39.886 dB and shifts QF=5 errors from 12 to 11 out of 32; all other sampled QFs are identical in BER.
2. At d1=90, removing d2 raises clean-image PSNR from about 31.80 to 32.06 dB without changing K-means BER at tested QFs.
3. Fast mode without coefficient shuffling closely matches common d2=0 BER and PSNR for d1=36 and d1=90. This does NOT establish security equivalence or universal behavior.
4. For d1=36 at QF=15 and 20 and for d1=90 at QF=5, K-means output is the bitwise complement of the 32-bit payload. Oracle inversion would yield 0 errors, but cannot be used as an actual blind decoder.
5. The simple 0.5-threshold decoder yields 16/32 errors in several low-QF conditions and can be worse than K-means. Hence labeling K-means as the sole failure is unjustified.
6. Under strong JPEG compression, mean scores for true-bit 1 can become lower than for true-bit 0; e.g. common (36,20) QF15 true-0 mean ~0.372, true-1 mean ~0.303. This supports a polarity-inversion phenomenon.
7. An implementable polarity resolution method would need additional independent information such as pre-agreed pilot bits, with overhead and independent evaluation. Ground-truth-based inversion is not such a method.

## Scope

Single image, one 32-bit payload, no multi-image statistical significance. No claim that d2 or shuffling is generally dispensable; no PSNR constrained optimization performed.

See [results.csv](results.csv) for all 48 rows and bit outputs. GitHub Actions artifact also contains attacked images and machine-readable manifest.
