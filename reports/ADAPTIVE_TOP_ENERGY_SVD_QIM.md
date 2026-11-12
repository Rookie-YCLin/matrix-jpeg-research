# Content-adaptive top-energy SVD-QIM

## What changed

The prior sparse-margin algorithm selected positions by a fixed 1-in-32 cycle. This new blind algorithm selects positions from image content. For each channel and each repeated payload bit, it ranks all candidate DCT-SVD blocks by their dominant singular value `sigma_1` and embeds only in the seven largest. It uses `d1=720` in selected blocks, leaves `sigma_2` unchanged, and leaves every non-selected block untouched. At extraction it recomputes the same ranking from the attacked image and votes only with those selected blocks.

The extractor has no original image, expected payload, or JPEG-QF input. The top-energy rank can change after JPEG, so this remains an empirical algorithm rather than a guaranteed matched selector.

## Matrix rationale

For a selected block `A=U Sigma V^T`, changing its first singular value gives

`A' - A = U(Sigma' - Sigma)V^T`, hence `||A'-A||_F^2 = sum_j (sigma'_j-sigma_j)^2`.

Non-selected blocks have exactly zero local spectral perturbation. A QIM period of 720 gives a local ideal decision margin of 180, compared with 22.5 for G6's 90. The top-energy rule concentrates the strong marks into blocks whose dominant component is large; that is a hypothesis for attack stability and perceptual masking, not a proof. JPEG may perturb singular values and change rankings, so BER and PSNR are measured rather than inferred from the inequality.

## Fixed primary-image measurements

| Algorithm | PNG PSNR | QF5 | QF10 | QF15 | QF20 |
|---|---:|---:|---:|---:|---:|
| G6, all blocks d1=90 | 31.801 dB | 32/32 | 0/32 | 0/32 | 0/32 |
| Fixed sparse margin, 13 replicas/channel | 31.083 dB | 0/32 | 0/32 | 0/32 | 0/32 |
| **Adaptive top-energy, 7 replicas/channel** | **31.191 dB** | **0/32** | **0/32** | **0/32** | **0/32** |

The adaptive candidate is 0/32 at PNG and every QF in the existing QF5,10,...,95 grid. It improves PNG PSNR by 0.108 dB over fixed sparse margin while using about half as many strong replicas per channel. It remains below a 35 dB target and is not claimed optimal.

External local validation of seven additional user-provided images also gave 0/32 at PNG, QF5 and QF15. Its PNG PSNR ranged 31.077--36.195 dB (mean 33.169 dB). This is evidence beyond the primary image, but is still too small and too image-specific to establish broad generalization.

## Reproduction

```text
python -m experiments.paper_low_qf --output-dir outputs/adaptive-top-energy-local --variants adaptive_top_energy720 --qualities 5 10 15 20 25 30 35 40 45 50 55 60 65 70 75 80 85 90 95
python -m pytest -q
```

Primary evidence: [QF5--20 CSV](../outputs/adaptive-top-energy720-replay/results.csv) and [full-grid CSV](../outputs/adaptive-top-energy720-replay-grid/results.csv). External validation remains local because it derives from user-provided images.
