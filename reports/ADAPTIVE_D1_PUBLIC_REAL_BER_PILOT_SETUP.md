# Public-image cross-image pilot: JPEG baseline and real-BER CI runner

Date: 2026-11-13

## Existing empirical observations (no watermark embedded)
The 12 independently named sample images under the public-image pilot produced 72 *actual* source-image JPEG QF5–10 encodes. QF5 and QF10 source-reconstruction PSNR have Spearman rank correlation **0.9790209790** and Pearson correlation **0.9905727335** across these 12 images. QF5 PSNR spans 20.54389 dB (grass) to 31.75977 dB (clock). These numbers describe **unmarked source JPEG distortion only**; they do not establish BER robustness, optimal d1, or 90% watermarking hit rate.

## Newly committed real-watermark workflow
File: `.github/workflows/adaptive-d1-public-pilot.yml`.

The workflow installs pinned `blind_watermark` upstream commit `322c90dc02d45644692095b34d3a6b735b6edbd8` plus compatible dependencies, generates scikit-image sample images, selects astronaut/chelsea/coffee, runs unit tests, and then calls `experiments.adaptive_d1_multimage_grid` for d1=1..24, QF=5..10. This entails up to **72 candidate embeddings and 432 JPEG attacks**, and uploads per-image BER/PSNR CSVs as an Actions artifact.

**Execution status at report creation:** workflow YAML committed; no confirmed workflow run or actual new watermark BER output. GitHub connector returned no associated PR-triggered runs for workflow creation commit. The GitHub Actions workflow may need to be manually dispatched from the Actions tab, or enabled by repository settings. Never treat its planned evaluation count as completed measurements.

## Constraints and follow-up
- d1=1..24 is a **pilot subdomain** and cannot produce an oracle over d1=1..150; do not compute full-domain hit rates from it.
- If pilot succeeds, extend to 1..150 on several new images and use the multi-image replay to calculate exact and epsilon-hit rates at a fixed 24-query budget.
- Keep scikit-image source and licensing manifest with each image; independently check rights before redistributing sample images.
- The previous 100 synthetic landscape near-hit rate of 98% at 48 evaluations is not cross-image BER evidence.
- The original image was already used for optimizer tuning; it must be excluded from independent-image success-rate denominators.

## User-facing commands
```bash
python -m experiments.adaptive_d1_public_image_corpus --output-dir /tmp/adaptive-d1-public
python -m experiments.adaptive_d1_multimage_grid --input-dir /tmp/adaptive-d1-pilot-input --output-dir /tmp/adaptive-d1-pilot-results --d1-start 1 --d1-stop 24
```

Workflow: `https://github.com/Rookie-YCLin/matrix-jpeg-research/actions/workflows/adaptive-d1-public-pilot.yml`.
