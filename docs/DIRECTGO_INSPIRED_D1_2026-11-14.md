# DIRECTGO-inspired integer d1 optimization pilot (2026-11-14)

## Motivation and attribution

Upstream: [blockchain-group/DIRECTGO](https://github.com/blockchain-group/DIRECTGO),
especially [Algorithms/dX_DTC_GL.m](https://github.com/blockchain-group/DIRECTGO/blob/main/Algorithms/dX_DTC_GL.m).

Paper: L. Stripinis and R. Paulavičius, *A practical DIRECT-type algorithm for medium-scale black-box global optimization*, Applied Soft Computing (2026), doi:10.1016/j.asoc.2026.116392; arXiv:2609.09796.

This is an **independent, Python, integer-domain, DIRECTGO-inspired adaptation**, **not** a port, reproduction, or validation of published X-DTC-GL results. DIRECTGO is MATLAB/MIT licensed; our code is independently written and does not copy upstream source.

## Fixed task (identical to V2)

- Black-box variable: integer `d1` in `[1,720]`, fixed `d2=20`, no user-configured grid.
- Eligibility: `d1=720` is evaluated first and must pass clean extraction and **all nine** frozen QFs (5,10,15,20,30,50,70,90,95).
- Among measured feasible candidates, choose maximum *pre-JPEG watermarked PNG PSNR*, with integer `d1` as tie breaker.
- Exactly 36 unique `d1` evaluations per admitted image, identical to `experiments/auto_zero_ber.py` V2.
- Reject nonzero worst-QF BER or nonzero clean extraction errors. Never infer unmeasured zero BER.

## Strategy

1. Evaluate anchor 720 and the root cell's center.
2. Partition one-dimensional integer cells into three balanced, contiguous children, preserving their measured center; two-point cells bisect.
3. Represent cells by measured center values, their width, and a *strictly heuristic* scalar ordering: feasible uses `-PSNR`, infeasible uses a high penalty plus observed BER and clean error count. The penalty is **not** the scientific objective.
4. Select cells using width/score Pareto nondominance and alternation among local quality, transition-aware refinement, and periodic widest-cell global exploration. No BER monotonicity assumption.
5. Optionally propose an additional integer from a 3-point convex quadratic model, **only** if all three adjacent measured points are already feasible and the model predicts improvement. Every such candidate still receives a real nine-QF JPEG evaluation. This is inspired by X-DTC-GL's dynamic local models, but adapted conservatively for discontinuous feasibility.
6. Keep the highest measured feasible PNG PSNR including the anchor.

This **does not implement** DIRECTGO's original Global-Local selection rules exactly, or its SQP hill-climber; SQP on an integer discontinuous BER objective is inappropriate. It tests whether DIRECT *ideas* improve the actual constrained search.

## Reproduce

Policy-only quick checks:

```bash
python -m pytest -q tests/test_direct_d1.py tests/test_auto_zero_ber.py
```

Real JPEG (pinned dependencies as recorded by `.github/workflows/direct-d1-pilot.yml`):

```bash
python -m experiments.adaptive_d1_public_image_corpus --output-dir /tmp/direct-images
python -m experiments.direct_d1_pilot --input-dir /tmp/direct-images --output-dir /tmp/direct-results
```

The runner archives `per_d1.csv`, `per_qf.csv`, `trace.csv`, `result.json` per image, including SHA-256, candidates, reasons, QF list and cost. For a fair runtime comparison use equal hardware; independent workflows have potentially different machine load.

## Comparison plan and decision rule

Compare directly with the previously verified V2 (36 evaluations/image) and historical sparse 68-point grid on the **same** three images and QFs:

| Image | Measured V2 d1 | Measured V2 PNG PSNR (dB) | Measured 68-point grid PSNR (dB) |
| --- | ---: | ---: | ---: |
| astronaut | 159 | 25.6963 | 25.6145 |
| chelsea | 143 | 27.2230 | 27.0836 |
| coffee | 96 | 31.0495 | 30.9425 |

The DIRECT-inspired method's real-JPEG results **must remain unreported until the CI jobs terminate and artifacts are read**. Main metrics: nine-QF feasibility, maximum measured feasible PNG PSNR, unique `d1` evaluations, actual JPEG attack count, recorded computation seconds, and success on disconnected feasible regions. The baseline does full nine-QF evaluation per step, so both methods have 324 JPEG attacks per qualified image at 36 candidates; reducing JPEG attack count requires a separate early-rejection evaluator.

Known limitation: the discontinuous zero-BER boundary makes parabolic prediction fragile. The method is not guaranteed to find the global optimum; a result inferior to V2 must be preserved, not cherry-picked.
