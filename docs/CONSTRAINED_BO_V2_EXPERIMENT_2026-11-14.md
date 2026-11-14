# CBO V2: pre-registered failure-aware integer Bayesian optimization test

Date: 2026-11-14. This second-stage test was designed following the **negative CBO V1 real-JPEG results**. This document defines its hypotheses and parameters **before** the new real-JPEG workflow finishes.

## First-stage observations

Prior CBO V1 found valid zero-BER solutions in astronaut / chelsea / coffee but with lower PSNR than V2 and more JPEG evaluations. In all three trajectories it repeatedly evaluated d1=37,38,39,..., although lower-step neighborhoods kept failing. This does **not** disprove Bayesian optimization: it exposes the insufficiency of the classifier probability and unconstrained-PSNR-driven EI when very high-PSNR candidate steps are likely infeasible.

## Testable hypotheses

1. A stronger feasibility exponent in constrained EI discourages expensive evaluation in known failing neighborhoods, reducing repeated-neighbor failures.
2. A small continuous distance-based penalty around *observed* failed candidates reduces wasted consecutive searches without hard-excluding potentially disconnected feasible islands.
3. Alternating GP acquisition with unsampled-gap midpoints between feasibility transitions and **both-failed endpoints** gives an exploration mechanism for narrow disconnected islands (coffee is the crucial failure case).

## Prespecified CBO V2 implementation

- **One integer variable d1** in [1,720]; d2=20 constant; same all-nine-QF + clean zero-BER hard constraint as V1.
- **Same initialization as the V2 comparator**, in the same order: d1 = (720,1,4,16,64,128,256,512). Each method evaluates 36 distinct candidates total.
- GP regression on all measured PSNR values, Matérn-3/2 with normalized length scale 0.12.
- GP binary classification for joint nine-QF zero-BER feasibility, Matérn-3/2 length scale 0.06.
- Acquisition when feasible incumbent exists: EI(PSNR) × P(full verified feasibility)^4 × soft novelty × soft distance from observed failures.
- Cold start with no feasible solution: probability-weighted surrogate uncertainty; never automatically stop because one designated anchor fails.
- Every fourth post-initialization experiment: unsampled interval midpoint. Alternate feasibility-boundary transitions and both-failed interiors. This is a deliberately hybrid, feasibility-aware **Bayesian optimization acquisition policy**, not pure classical cEI.
- Hard feasibility is *never inferred from models*. Only clean extraction plus **nine actually measured zero-error JPEG QFs** can certify any recommended d1. First failed QF early-rejects an infeasible candidate; skipped QFs remain unknown.
- Prespecified 36 unique d1 budget. No global-optimality guarantee.

## Evidence and fair comparison

Run the real JPEG paired CBO V2 vs **unchanged V2** search on seven existing public images:

astronaut, chelsea, coffee, camera, coins, moon, rocket.

For each image, use the same pinned guofei watermark code, image/payload/keys, Pillow JPEG encoder, QF schedule, early-rejection evaluator, and 36 candidate budget. Match **domain and initial points** to V2, unlike the original V1 experiment.

Record real measured best feasible d1, embedded PNG PSNR, full verified feasibility, every attempted QF, total JPEG checks, wall time, and candidate trace. Compare both (i) per-image and (ii) seven-image totals. GP computation time is included in wall time. One run/image is not a stability benchmark; repeat trials and sensitivity analysis are needed before broad claims.

## Risks and interpretation

The exponent 4, fixed length scales, distance weights, and coverage period are experimental design decisions, **not derivations from Bayesian posterior decision theory**. They may improve, worsen, or merely shift exploration behavior. The heuristic interval probes increase robustness to model misspecification but also reduce the budget for GP proposals. Even matching V2 on one dataset cannot establish cross-image superiority.

CBO V1 remains preserved in PR #47. CBO V2 is a separate child research PR; do not merge either without inspecting archived actual-JPEG measurements.

## Execution

```bash
python -m pytest -q tests/test_constrained_bo_d1_v2.py
python -m experiments.adaptive_d1_public_image_corpus --output-dir /tmp/input
python -m experiments.constrained_bo_d1_pilot --input-dir /tmp/input --output-dir /tmp/cbo2 --bo-version v2 --compare-v2
```
