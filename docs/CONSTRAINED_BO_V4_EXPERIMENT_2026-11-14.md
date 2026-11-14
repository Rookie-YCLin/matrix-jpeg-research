# CBO V4: verified-feasibility warm-start, then constrained Bayesian optimization

## Status and motivation

**Experimental implementation. Not yet empirically proven better than the legacy V2 baseline.** Earlier CBO experiments must be retained as negative evidence:

- CBO V2: 3/7 wins vs unchanged legacy V2 (seven development images); coffee underperformed.
- CBO V3: astronaut −0.0432 dB, coffee −4.2249 dB, rocket +5.6671 dB (all actually nine-QF certified), while repeatedly evaluating infeasible small d1.
- CBO V3.1: five **new images**, clock/page/text/brick/grass, lost all five to legacy V2 despite 50 passing policy tests and completed actual-JPEG paired jobs (workflow 43581983728).

These failures expose an acquisition allocation issue: EI × joint feasibility can devote many expensive evaluations to very low d1 where measured QF5 failures recur. Merely increasing/down-weighting distance penalties does not establish an effective optimizer.

## Preregistered V4 design

V4 is **two-stage feasible-incumbent-first BO**:

1. **Phase I: 18 measured d1 evaluations** including the exact common eight anchors `(720,1,4,16,64,128,256,512)`. The next 10 candidates use the **unchanged legacy V2 `_next_candidate` policy**, adapted from actual measured, fully certified observation objects. This efficiently refines observed feasibility transitions and can search disconnected gaps. It is not claimed monotone or globally optimal.
2. **Phase II: 18 further measured d1 evaluations** using Gaussian Process Regression on measured PNG PSNR, Gaussian Process Classification on the **joint all-nine-QF success** label, and separate per-QF partial-observation exploration and gap probes. The EI score also uses V3.1's *same-first-failed-QF repeated-failure saturation*, never hard-excluding integer candidates.

For a source image with **no verified feasible point**, Phase I uses the GP-based fallback instead of assuming that d1=720 passes; no synthetic or unverified incumbent is created.

The final answer is the best actually measured **clean + all-nine-QF zero-BER** candidate among all 36, irrespective of method that proposed it. This is a hybrid search, not canonical pure BO, and theoretical guarantees for ordinary constrained EI cannot be asserted. Because the warm-start uses 18 and not all 36 legacy candidates, V4 is **not guaranteed** to match even the full 36-evaluation legacy V2 baseline; that must be measured.

### Objective and budget

- Integer `d1 in [1,720]`, fixed `d2=20`, 36 distinct evaluations (8 geometric anchors + 10 deterministic warm-start refinements + 18 BO).
- Actual watermark embedding/extraction and Pillow JPEG at QFs `5,10,15,20,30,50,70,90,95`.
- BER=0 for clean and every tested required JPEG QF is mandatory to recommend a d1.
- Early-rejection unmeasured QFs remain missing/None and are not imputed.
- Measure pre-JPEG watermarked PNG PSNR against original.
- Preserve upstream pinned guofei commit and payload settings.

## New-image validation plan: freeze before results

Earlier studies have used 12 scikit-image sample images:
`astronaut, camera, chelsea, coffee, coins, moon, rocket, clock, page, text, brick, grass`.
None may be called held out for V4.

V4's **four preselected unused images** from scikit-image 0.24.0:

`colorwheel, hubble_deep_field, immunohistochemistry, human_mitosis`.

`colorwheel` is a color synthetic-pattern sample (not a natural photograph). The other three cover astrophotography, histological tissue and microscopy. The image generator saves unresized RGB PNG (only grayscale channel duplication where needed), source shape and SHA256. No held-out source may be used to retune V4 without explicitly invalidating its held-out status.

For each image, CI runs **V4 vs unchanged legacy V2** in the same process and stores candidate-by-candidate CSV, per-QF errors, trace, winner and actual costs. The eight initial candidates and 36-candidate budget are identical. Compare:
- Best *verified* feasible PNG PSNR, including missing feasible result as a separate failure outcome;
- number of actual JPEG checks, wall-clock time;
- whether V4 uses its BO phase to improve upon its own Phase-I incumbent;
- image-wise paired delta and aggregate mean and median, without claiming significance from four images.

**Stop criterion:** If the new-image results do not outperform legacy V2 in a robust manner, report failure and retain the draft PR. Do not claim success by selecting only rocket-like examples or tuning on the four new images.

## Files

- `experiments/constrained_bo_d1_v4.py` – phase I and phase II selector.
- `experiments/constrained_bo_d1_pilot.py` – real-JPEG adapter `--bo-version v4`.
- `tests/test_constrained_bo_d1_v4.py` – synthetic policy and equivalence checks, not JPEG performance evidence.
- `experiments/constrained_bo_d1_v4_new_corpus.py` – four fixed untouched source images.
- `.github/workflows/constrained-bo-v4-new-images.yml` – policy tests and real-JPEG paired jobs.

## Reproduction

```bash
python -m pytest -q tests/test_constrained_bo_d1_v4.py tests/test_constrained_bo_d1_v3.py tests/test_constrained_bo_d1_v2.py tests/test_constrained_bo_d1.py tests/test_early_reject_policy.py
python -m experiments.constrained_bo_d1_v4_new_corpus --output-dir /tmp/cbo-v4-source
python -m experiments.constrained_bo_d1_pilot --input-dir /tmp/cbo-v4-source --output-dir /tmp/cbo-v4-paired --bo-version v4 --compare-v2
```
