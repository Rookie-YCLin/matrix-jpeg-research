# Adaptive d1 — independent-image validation protocol and implementation (2026-11-13)

## Why this is the next experiment
The existing 200-seed / 270-configuration optimizer sweeps reuse **one** measured image. A 100% hit for the deterministic n=8 nearest-neighbor strategy is an in-sample property, not a 90% unseen-image success rate. The previous 14-objective stress test is likewise not 14 independent images.

## New code
- `experiments/adaptive_d1_multimage_grid.py`: resumable **real** watermark embedding, PNG PSNR, six QF5–10 JPEG attack/extraction measurements per integer d1, by image. Uses `experiments.adaptive_d1_grid.evaluate_d1` and `summarise`, preserving the pinned core and fixed 32-bit payload, d2=20 and JPEG settings.
- `tests/test_adaptive_d1_multimage_grid.py`: mock-based regression tests for resume behavior, no duplicate d1 evaluation, and rejection of changed d1 domain.

**Status:** code committed to the research branch; this environment could not access the public repository over the container network, so no new independent-image JPEG experiment or pytest execution is claimed. These tests must run in a full repository environment with its pinned dependencies.

## Suggested command
```bash
python -m experiments.adaptive_d1_multimage_grid \
  --input-dir data/evaluation_images \
  --output-dir outputs/multimage-qf5-10 \
  --d1-start 1 --d1-stop 150
pytest -q tests/test_adaptive_d1_multimage_grid.py
```

Each image receives a SHA256-identified output directory and per_d1.csv. Completed d1 values are skipped on resume. The manifest JSONL is an **execution log** (may contain repeated entries on rerun); the per-image source.json and per_d1.csv are authoritative.

## Evaluation metrics
For each independent test image i, calculate a full 150-point Grid oracle J_i* under the pre-registered Model B objective (lambda=.5, PSNR threshold 40 dB).

- Exact hit: `J_i(d_selected) == J_i*` within float tolerance, including ties.
- Near hit: `J_i(d_selected)-J_i* <= epsilon` for a fixed, predeclared epsilon. Proposed reporting epsilon=0, 0.005, 0.01 separately, not switching epsilon after viewing test results.
- Also report BER mean/worst, PSNR, d1, objective regret, evaluation count, wall time, and whether Model A was infeasible.

**Critical:** 90% means at least 9 of 10 held-out images, NOT 180/200 random seeds on one image. With only 10 held-out images the uncertainty is large; report counts and confidence intervals, and consider a larger independent test set if resources permit.

## Hold-out and optimizer selection
1. Curate at least 50 genuinely distinct, licensed images, preserve source URL/license/SHA256, then freeze 30 train / 10 validation / 10 test splits. The current repository does not contain that complete dataset.
2. On train: exploratory method design. On validation: select among frozen candidate configurations n=8,k=1,width=1; n=8,k=2,width=1; stratified jitter+refine; fair BO/DE/PSO. Do not retune after inspecting test outcomes.
3. On test: run each selected algorithm at exactly 24 distinct d1 queries; calculate Grid oracle separately for audit only. The optimizer cannot access unqueried Grid values during search.
4. The test oracle computation is an expensive **benchmark**, not the online deployment algorithm. A truly zero-repeat-test predictor needs a separate image-feature model and a decodable d1 communication protocol.

## Cost and limitations
The single-image exhaustive 150-point Grid previously took ~1559 seconds; 50 images could require ~22 hours or more, depending on resolution and hardware. Run a pilot of 2–3 images before the full dataset and use resume. Each candidate entails six JPEG attacks and blind extractions; avoid treating lookup replay time as production time.

## Research decision rule
Do not claim 90% until independent-image test data exists. If a robust 24-evaluation optimizer fails, test a predeclared budget increase or relax epsilon (as a separately reported metric), rather than hiding failures. If oracle d1 shifts sharply with image content, prioritize feature-based d1 prediction or a multi-region optimizer; if no 40dB / low-BER feasible point exists, report infeasibility instead of promising a zero-BER solution.
