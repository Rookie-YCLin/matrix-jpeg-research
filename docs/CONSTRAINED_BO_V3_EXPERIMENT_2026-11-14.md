# Constrained BO V3: partial-JPEG-QF evidence and mixed discrete exploration

**Status:** implementation + synthetic policy tests + real-JPEG CI protocol. A successful commit does **not** mean that V3 has passed CI or outperformed V2. Treat this as an experimental branch and keep the PR in draft until actual artifacts are inspected.

## Motivation and empirical baseline

V2 employs `EI(PSNR) * P(all nine QFs pass)^4` with failure-neighbor repulsion and periodic interval probes. In the seven-image paired real-JPEG result, V2 beat legacy V2 on three images and lost on four. Coffee: the joint-zero-BER feasible `d1=96` yields 31.049474 dB, while `d1=99` fails QF5 and CBO V2's best was `d1=164` / 27.036721 dB. Rocket improved under CBO V2. A failed point is not proof its integer neighbors fail.

Existing evidence: [V2 trial](CONSTRAINED_BO_V2_RESULTS_2026-11-14.md). These seven images are **development data**, not held-out validation.

## Fixed experimental objective

- Optimize only integer `d1 in [1,720]`; `d2=20` stays fixed.
- A valid candidate must have **zero clean bit errors** and actually observed **zero bit errors at all** QFs `(5,10,15,20,30,50,70,90,95)`.
- Measure PNG PSNR of the pre-JPEG watermarked image.
- Exactly the same eight initial anchors `(720,1,4,16,64,128,256,512)`; 36 distinct candidate evaluations.
- Continue using the pinned guofei watermark implementation, Pillow JPEG and existing early-rejection evaluator. A candidate may be rejected at the first failed QF.
- Never infer or impute BER for skipped QFs.

## V3 model, acquisition and exploration

1. **Objective surrogate:** GP regression on all observed PNG PSNR with normalized d1 and fixed Matérn-3/2 scale 0.12, copied from V2. Its EI is measured relative only to the best **fully verified feasible** observed candidate.
2. **Main hard-constraint surrogate:** one GPC trained on the binary label `clean + all nine QFs actually passed`, Matérn-3/2 length scale 0.06. This is the **joint** feasibility label; V3 does not multiply nine marginal QF probabilities.
3. **Main acquisition:** `EI(d1) * P(joint verified success | d1)`. The exponent-4 penalty and the failure-neighbor repulsion from V2 are deliberately removed. This is a testable ablation, not an asserted improvement.
4. **Partial-QF auxiliary exploration:** each measured QF contributes its **actual integer bit error count** in `qf_error_counts`. Missing QF outcomes are `None`. For each QF, local Gaussian-kernel weights (scale 18 integer d1 steps) and Beta(1,1) pseudo-counts yield an *exploration variance score*. These locally weighted values are heuristics, **not calibrated posterior probabilities** and are never used as a replacement for hard success certificates.
5. **Gap exploration:** probes previously untested interval midpoints, including intervals with two failed endpoints. It uses only observed joint statuses and QF outcomes known on both endpoints. No monotonic BER assumption.

After initialization, V3 allocates every fourth selection to QF-information exploration (round index % 4 == 2), every fourth to gap exploration (round index % 4 == 0), and the other two to joint constrained EI. If no gap is eligible it falls back to EI. All 720 integer candidates remain eligible until tested; deterministic ties and no duplicate evaluations.

### Model/data limitations

- Per-QF evidence is missing by design after early rejection. Missingness is not random; the auxiliary local scoring is explicitly heuristic and should **not** be interpreted as a calibrated estimate of `P(all QFs pass)`.
- Because only up to 36 d1 values are evaluated, small feasible islands can still be missed. No global-optimality guarantee is claimed.
- The GP and kernel hyperparameters are predeclared here for this version; do not retune after viewing the three-image outcomes and call them held-out evidence.
- V3 intentionally does **not** claim measured time savings or higher PSNR until GitHub Actions completes and the artifacts are audited.

## Code changes

- `experiments/constrained_bo_d1_v3.py` — V3 selector and partial evidence validation.
- `experiments/early_reject_d1_pilot.py` — additive `qf_error_counts` field containing only truly measured JPEG extractions. Existing V1/V2 selector behavior is unchanged.
- `experiments/constrained_bo_d1_pilot.py` — `--bo-version v3` adapter to the existing real-JPEG paired trial and archival format.
- `tests/test_constrained_bo_d1_v3.py` — synthetic tests, **not** JPEG efficacy evidence.
- `.github/workflows/constrained-bo-v3.yml` — policy tests followed by three-image real-JPEG paired trials.

## Acceptance and comparison

1. Require the synthetic policy tests and all three real JPEG jobs (astronaut, coffee, rocket) to pass.
2. Inspect every archived `per_d1.csv`, `per_qf.csv`, `trace.csv`, `result.json` and `comparison.json`. Count exactly 36 unique d1 for each method; confirm all winners are fully verified.
3. Compare PSNR differences in dB **and** actual JPEG checks and wall time; report negative findings. JPEG checks can rise when more feasible candidates receive full nine-QF verification.
4. Keep this PR draft pending a separately frozen, *new-image* confirmatory evaluation. Seven previously analyzed images remain development images.

## Reproduction

```bash
python -m pytest -q tests/test_constrained_bo_d1_v3.py tests/test_constrained_bo_d1_v2.py tests/test_constrained_bo_d1.py tests/test_early_reject_policy.py
python -m experiments.adaptive_d1_public_image_corpus --output-dir /tmp/bo-input
python -m experiments.constrained_bo_d1_pilot --input-dir /tmp/bo-input --output-dir /tmp/bo-v3 --bo-version v3 --compare-v2
```

Run only after installing exactly the dependencies and pinned guofei commit specified in `.github/workflows/constrained-bo-v3.yml`. This reproduces real JPEG, not a BER simulator.
