# Automatic zero-BER region search — pilot results (2026-11-13)

## Scope and evaluation protocol

This report concerns an **empirical, fully automatic** selector for the *first*
SVD-QIM quantization step d1, not a new SVD embedding algorithm or a theorem.
It receives an evaluator callback but **no user-provided d1 candidates, step
spacing, search bounds, or d1 tuning**. Internal frozen choices are a per-image
d1=720 eligibility/fallback check, 36 unique evaluations, geometric startup
probes, and feedback-driven interval refinement with periodic exploration.

- Repo research branch: research/auto-zero-ber-region-search-20261113
- PR: https://github.com/Rookie-YCLin/matrix-jpeg-research/pull/43
- Baseline 68-candidate sparse grid: https://github.com/Rookie-YCLin/matrix-jpeg-research/actions/runs/43361158313
- V1 measured pilot: https://github.com/Rookie-YCLin/matrix-jpeg-research/actions/runs/43375602044
- V2 measured pilot: https://github.com/Rookie-YCLin/matrix-jpeg-research/actions/runs/43376226724
- V2 measured source commit: 330da683635cc74f000b6965c9a59d2770e6eb74
- Source images: scikit-image astronaut (512x512 RGB), chelsea (300x451 RGB), coffee (400x600 RGB); see artifacts for SHA-256.
- JPEG QF: {5,10,15,20,30,50,70,90,95}. Fixed d2=20. The existing upstream blind_watermark, watermark payload, keys, JPEG encoder, and other pipeline conditions are inherited from the original grid evaluator.
- Qualifying feasibility: zero clean extraction errors **and** zero bit errors at **every** tested QF. PSNR measured on watermarked PNG **before JPEG**, not the attacked JPEG.
- Each auto run: 36 unique d1 evaluations, 324 full JPEG attacks per image. Legacy baseline: 68 d1 evaluations / 612 attacks per image. Reduction: (68-36)/68 = 47.06%.

## Measured outputs (all selected d1 feasible in the nine-QF protocol)

| image | sparse 68-grid best d1 | baseline PNG PSNR (dB) | V1 best d1 | V1 PNG PSNR (dB) | V2 best d1 | V2 PNG PSNR (dB) | V2 minus sparse baseline |
|---|---:|---:|---:|---:|---:|---:|---:|
| astronaut | 161 | 25.6145 | 159 | 25.69627565 | 159 | 25.69627565 | +0.0818 dB |
| chelsea | 145 | 27.0836 | 143 | 27.22300838 | 143 | 27.22300838 | +0.1394 dB |
| coffee | 97 | 30.9425 | 163 | 27.08244513 | 96 | 31.04947374 | +0.1070 dB |

The V1 coffee failure was a substantive negative result: restricting detailed
search to the first feasible transition near d1=163 skipped a lower disconnected
zero-BER island near d1=96–97. The V2 policy now examines intervals whose
*two endpoints have failed*, especially below the current best measured
feasible d1, instead of spending many evaluations above the incumbent.

V2's coffee improvement is **in-sample** because the new search rule was
motivated by V1's failure on that same image. The three-image results are
reproducible pilot evidence, **not** independent generalization validation.

## Important data-provenance detail

The V2 workflow run 43376226724 was triggered from source commit
330da683635cc74f000b6965c9a59d2770e6eb74, but its automatically archived
manifest accidentally retains the string "auto_zero_ber_v1" as the method label.
The actual policy is V2 as identified unambiguously by the commit SHA and
candidate trace. The manifest field has since been corrected in source on
the same PR. Do not silently relabel or overwrite the original artifact.

## Mathematical motivation

For A = U Σ Vᵀ, a fixed-U,V singular-value modification obeys
||A'-A||_F² = ||Σ'-Σ||_F². Under JPEG-induced perturbation E,
|σ_i(A+E)-σ_i(A)| <= ||E||_2. These motivate prioritizing measured BER
feasibility and PSNR; they **do not** prove BER monotonicity, that PSNR is
strictly monotonic in d1, or global optimality. The optimizer therefore
uses *observed* feasibility plus exploration instead of analytic threshold
assumptions.

## Next scientific steps

1. Verify the corrected-manifest workflow reaches terminal success; preserve
   the V1 and V2 trace files and run IDs.
2. Freeze the V2 policy and validate on **held-out eligible public images**;
   count ineligible images separately. Do not retune on test images.
3. Compare fairly with fixed-grid/random and multi-region/PSO baselines at
   identical numbers of expensive d1/JPEG evaluations.
4. Repeat with alternative seeds / payloads only as predeclared experiments;
   do not claim all-QF or all-image zero BER.
5. Keep results in draft PR until review.
