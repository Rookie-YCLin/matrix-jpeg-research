# AMRS: competing-region integer d1 search — first executable benchmark

Date: 2026-11-13

## New algorithm
`experiments/adaptive_d1_adaptive_regions.py` implements Adaptive Multi-Region Search (AMRS):
1. 8 uniform coarse anchors.
2. Identify up to 3 separated promising basins using **observed** scores only.
3. Prioritize basin centers using observed score plus a modest visit penalty, reducing premature concentration.
4. Every sixth refinement step, query the integer maximally distant from all previously evaluated integers.
5. Query the nearest as-yet-unseen integer to the chosen basin center.
6. Exactly one objective callback per unique integer; the full Grid is never accessed by the optimizer.

`tests/test_adaptive_d1_adaptive_regions.py` checks 24 unique evaluations, two-basin input, invalid parameters and NaN rejection. **Local Python run:** `3 passed in 0.07s` for a functionally identical standalone module. Full GitHub repository tests still need CI confirmation.

## Independent synthetic-function benchmark
`experiments/adaptive_d1_toy_benchmark.py` deterministically generates 100 different three-basin 1D objectives using Python `random.Random(901)`, each with distinct basin positions/widths/floors and a sinusoidal ripple. The exact discrete oracle is evaluated over integers 1..150. The algorithms only receive 12, 24, or 48 objective queries.

| Budget | Fixed single basin near hits | Fixed dual basin near hits | AMRS near hits |
|---|---:|---:|---:|
| 12 | 44/100 | 45/100 | 47/100 |
| 24 | 79/100 | **83/100** | 78/100 |
| 48 | 80/100 | 91/100 | **98/100** |

Near hit means objective regret <=0.01, **not exact d1 match**.

At 48 queries: AMRS mean regret **0.000687**; fixed dual basin mean regret **0.004426**; fixed single basin mean regret **0.008176**.

## Interpretation
AMRS benefits from greater budget, but is not uniformly superior: it trails fixed dual-region refinement at 24 queries. These are **synthetic functions** and are not evidence of cross-image JPEG BER robustness. The functions were generated to stress multiple basins; they are not calibrated to real watermarking objectives.

## Required next experiments
- On measured JPEG Grid for the existing image, compare AMRS with fixed single/dual region and fair BO/DE/PSO at 12/24/48 evaluations, recording exact and epsilon-regret.
- Run at least 10 new, independent image Grids and freeze algorithm settings before test; 90% means >=9/10 distinct images, not 90% of seeds on one image.
- For actual deployment, distinguish a 24/48-evaluation online search from image-only feature prediction without repeated JPEG.
- If AMRS loses at 24 evaluations on held-out images, retain the simpler dual-region method as the preferred low-budget candidate.

## Reproduction
```bash
python -m pytest -q tests/test_adaptive_d1_adaptive_regions.py
python -m experiments.adaptive_d1_toy_benchmark
```

The local execution used the same algorithm and test logic in a standalone directory because the full GitHub repository cannot be cloned from the current container (GitHub DNS unavailable). No new JPEG tests were run.
