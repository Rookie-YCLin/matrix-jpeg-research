# Adaptive d1: 14-objective sensitivity stress test (2026-11-13)

## Purpose
After observing a 100% in-sample oracle hit for the deterministic 8-coarse-point, 1-region, nearest-neighbor method, assess its sensitivity to the objective rather than mistake 200 repeated deterministic runs for independent validation.

## Data and protocol
Source: PR #39, 150 previously measured Grid points from ONE image, `per_d1.csv`. No new JPEG evaluations. Each objective reuses the same underlying mean BER, worst BER and PNG PSNR.

14 objectives:
- 12 combinations `lambda * mean_ber + (1-lambda)*max(0,(threshold-PSNR)/threshold)`, lambda in {0.25,0.5,0.75}, threshold in {35,38,40,42} dB.
- 2 risk combinations `0.25*mean_ber + 0.25*worst_ber + 0.5*max(0,(threshold-PSNR)/threshold)`, threshold in {38,40} dB.

All methods use exactly 24 **distinct** integer d1 lookups. Deterministic 8-point uniform initialization; refinement picks nearest unqueried integer to the current best region. Two-region mode alternates between two good regions separated by >10 in d1, recomputed from evaluated values. Regret = best queried objective minus full-grid oracle for **that same objective**. Different objective values are never directly compared.

## Results
| Strategy | Exact objective-oracle hits (of 14) | Mean regret | Maximum regret |
|---|---:|---:|---:|
| n=8, k=1, nearest | 7/14 | 0.02260501 | 0.08017201 |
| n=8, k=2, nearest, separation>10 | 4/14 | **0.01496216** | **0.04575775** |
| n=6, k=3, nearest, separation>10 | 5/14 | 0.01931518 | 0.07700775 |

The n=8 single-region strategy is better for exact hits across these 14 objectives; the n=8 dual-region strategy is better for average and worst regret. The apparent advantage of the latter is a *within-image objective stress test*, not independent generalization.

## Caveats and decision
1. The objectives are correlated because all derive from the same 150 measured points; **7/14 is not a 50% estimate for future images**, and cannot establish or reject the user's 90% new-image target.
2. Many configurations were examined on this same image, so this is still development-set exploration.
3. Single-region 200/200 hits on the original objective were deterministic repeats, not a meaningful 200-sample confidence estimate.
4. The 90% milestone should be pre-registered as image-level success under one fixed objective, fixed 24-evaluation budget and specified regret tolerance, measured on truly held-out images with an independent Grid oracle.
5. Next engineering action: acquire/curate new licensed images and run independent JPEG Grid sweeps; preserve existing pipeline parameters and audit fair evaluation counting.

## Source and reproducibility
The numerical stress test was executed by direct JavaScript evaluation of the GitHub `per_d1.csv` contents; this report is an empirical record. No local full-repository Python/JPEG execution is claimed.
