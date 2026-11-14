# CBO V2 seven-image paired real-JPEG findings (2026-11-14)

## Reproducible evidence

- GitHub Actions run: https://github.com/Rookie-YCLin/matrix-jpeg-research/actions/runs/43563959376
- Research PR (draft): https://github.com/Rookie-YCLin/matrix-jpeg-research/pull/48
- V1 predecessor: https://github.com/Rookie-YCLin/matrix-jpeg-research/pull/47
- Methods run side by side **on the same image, the same fixed d2=20 / payload / pinned upstream / Pillow JPEG / nine QFs / early-rejection evaluator**, with **identical 8 initial d1 candidates** `(720,1,4,16,64,128,256,512)`, integer domain `1..720`, and **36 distinct d1 evaluations each**.
- The initial test run failed due to literal Python `\\n` in the newly added file; commit `04faaab7dfcbb33218e322a28220fa7e28f2d79d` fixed it before this **successful** run. The CI policy job subsequently reported **36 passed**.
- All seven paired real-JPEG jobs ended **successfully**. The CBO V2 and comparator winners are actual, clean + nine-QF **zero-BER verified** candidates, not surrogate predictions.

## Exact observed quality and cost

| Image | CBO V2 d1 | CBO V2 PSNR dB | Existing V2 d1 | Existing V2 PSNR dB | ΔPSNR (CBO−V2) dB | CBO JPEG checks | V2 JPEG checks | CBO seconds | V2 seconds |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| astronaut | 160 | 25.653054 | 159 | 25.696276 | −0.043222 | 132 | 84 | 47.448 | 37.481 |
| camera | 151 | 23.201786 | 150 | 23.254323 | −0.052537 | 132 | 92 | 46.250 | 37.882 |
| chelsea | 139 | 27.366536 | 143 | 27.223008 | +0.143527 | 124 | 93 | 22.668 | 19.224 |
| coffee | 164 | 27.036721 | 96 | 31.049474 | −4.012753 | 124 | 93 | 41.536 | 35.169 |
| coins | 151 | 23.282752 | 150 | 23.364718 | −0.081967 | 132 | 92 | 20.912 | 17.310 |
| moon | 158 | 23.301368 | 156 | 23.240876 | +0.060492 | 132 | 100 | 31.806 | 26.596 |
| rocket | 76 | 31.735849 | 148 | 26.068767 | +5.667082 | 127 | 95 | 45.493 | 38.425 |
| **sum of checks / seconds** | — | — | — | — | — | **903** | **649** | **256.113** | **212.088** |

- CBO V2: 3/7 wins, 4/7 losses in PSNR against V2. Median per-image ΔPSNR **−0.043222 dB**, arithmetic mean **+0.240089 dB** (strongly affected by rocket +5.667).
- Actual JPEG attack/extraction count **+254 / +39.14%** (903 vs 649); summed per-image process duration **+44.025 s / +20.76%** (256.113 vs 212.088). These sums aggregate seven separate CI jobs and are **not** a measured end-to-end parallel workflow time or statistically significant runtime claim.
- A higher number of full nine-QF-successful candidates directly raises JPEG check count, because each accepted candidate must pass nine real checks; distinguish this from repeated unproductive low-step proposals.

## Diagnostically important actual checks

- **Rocket: CBO d1=76** gave **31.735848687 dB** and the real-job trace says **`QF_checks=9 full_feasible=True`**. The existing V2 method found d1=148 / 26.068766533 dB under the same candidate budget. This is a large quality improvement **on that particular image**, not a global optimum proof.
- **Coffee: CBO d1=99** gave high 30.7156 dB PSNR but **`QF_checks=1 full_feasible=False`**: it failed already at QF5. Yet the existing V2 found nearby **d1=96** with 31.049474 dB and full nine-QF zero BER. This illustrates the need for local integer exploration; merely extrapolating a smooth GP classification boundary may miss small feasible islands.
- Neither a failing neighbor nor a high PSNR implies the status of an untested integer d1.

## Interpretation

**The hypothesis that modifying our BO acquisition could reveal missed disconnected feasible islands received evidence on rocket and small wins on chelsea/moon, but the proposed CBO V2 is not superior overall.** Coffee remains a severe quality regression, with additional JPEG cost on all seven images. This evidence favors further diagnosis of the acquisition policy and modeling of the discrete feasibility landscape, **not abandoning Bayesian optimization**.

Our V2 acquisition is a **hybrid feasibility-aware BO policy**, with explicit coverage probes and distance heuristics; it should not be presented as unmodified canonical cEI or as having cEI's theoretical guarantees.

## Preregistered next research experiment (not yet completed)

1. **Do not re-tune repeatedly on these same seven outcomes and call them a held-out confirmation**; they have now become development images.
2. On *previously unseen images*, evaluate a BO acquisition that uses a local binary feasibility model with calibrated uncertainty or constraint-boundary learning, with frozen hyperparameters and protocol.
3. Separately measure **time per GP update, embeddings, JPEG evaluations**, and consider an acquisition that accounts for evaluation cost only if supported by that data.
4. Focus regression tests on **narrow feasible islands near failed integers** (e.g. d1=96 passing while 99 fails) and zero BER certificates requiring nine actual QF observations.
5. Record run seeds, image hashes and complete d1 / QF traces. Compare both overall PSNR distribution and cost, not just the best showcase image.

**Decision:** keep draft PR #48 unmerged, retain full positive and negative evidence, and consider further BO improvements before any claim of broader superiority.
