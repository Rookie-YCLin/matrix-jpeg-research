# CBO V4 four-image real-JPEG results — interim audit, 2026-11-14

## Provenance

Actual GitHub Actions: https://github.com/Rookie-YCLin/matrix-jpeg-research/actions/runs/43582772857

This report records only fully completed, actually executed same-image paired JPEG tests. The run initially failed while generating external scikit-image samples because the optional `pooch` dependency was missing; commit `2626b4b853b1ec08095054b39fbf2e7c61923c05` added that dependency without changing the algorithm or test images. New V4 job `policy-tests` completed successfully with 60 passing tests.

Both algorithms evaluate **36 distinct integer d1 candidates** on the same image, using d2=20, unchanged pinned guofei watermarking and Pillow JPEG pipeline; a winner is accepted only after clean and nine actual QF 5/10/15/20/30/50/70/90/95 zero-error extractions. The reported objective is pre-JPEG marked PNG PSNR, not attacked JPEG PSNR.

## Completed real JPEG comparisons (no synthetic outcomes)

| Previously unseen image | V4 best d1 | V4 PNG PSNR dB | Legacy V2 best d1 | Legacy V2 PNG PSNR dB | V4−V2 dB | V4 JPEG checks | V2 JPEG checks | V4 seconds | V2 seconds |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| colorwheel | 149 | 26.3492932797 | 149 | 26.3492932797 | 0.000000 | 116 | 100 | 28.463306 | 26.014280 |
| immunohistochemistry | 143 | 26.8360954368 | 143 | 26.8360954368 | 0.000000 | 108 | 92 | 75.091949 | 68.742843 |
| human_mitosis | 128 | 25.2589478594 | 128 | 25.2589478594 | 0.000000 | 100 | 68 | 72.074055 | 59.967538 |
| hubble_deep_field | *Job in progress at time of this report* | — | — | — | — | — | — | — | — |

### Interpretation

The three completed V4 new-image jobs **matched, but did not improve**, the best verified legacy V2 PSNR. Each spent more real JPEG checks and wall time. Thus the warm-start has preserved the legacy incumbent on these cases but has not shown benefit from the additional BO stage. The outcomes **do not establish that V4 is superior**.

The fourth image must be excluded from any success/failure count until its actual job finishes; never impute the result or assume a tie. No hyperparameters were retuned using these results. These four images were selected in the V4 protocol before CI, while the earlier 12 sample images had already entered BO development.

Archive per-d1, per-QF, trace and comparison files are available from the linked GitHub Actions job artifacts after job completion. Keep PR #51 draft and do not merge or claim a positive result without further evidence.

For historical context, V3.1 had **five losses in five previously unseen images** and its BO policy repeatedly sampled known unproductive low-step regions. The decision to warm-start V4 from the legacy feasible-boundary strategy was prompted by that negative evidence.

## Research decision

Use legacy V2 as the incumbent production/research baseline while the BO improvements remain experimental. If the final fourth-image result does not change the evidence materially, investigate better acquisition under a jointly modelled feasible objective rather than simply adding more distance penalties or raising the GP feasibility exponent.
