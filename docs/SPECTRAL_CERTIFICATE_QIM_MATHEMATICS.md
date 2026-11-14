# SVD-QIM adaptive step selection by exact finite-domain optimality certificates

## Research objective (not another BO variant)

Find a fully automatic d1 from the integer domain {1,...,720}, with d2=20 fixed, given a previously unseen image, a fixed 32-bit blind watermark, and a **strict actual zero-BER requirement on clean extraction and every Pillow JPEG QF {5,10,15,20,30,50,70,90,95}**. The output must be the best **genuinely verified** candidate for a specified image-quality objective; an estimated probability of feasibility is NEVER sufficient to certify a winner.

### Why the old GP/heuristic loop was not a suitable primary scientific method

Prior BO iterations repeatedly appended uncalibrated acquisition weights, local failure penalties, narrow-island exploration quotas and arbitrary warm-start allocations to address newly noticed failures. Passing unit tests did not improve validation PSNR. None of the arbitrary parameters addressed the fundamental distinction between (a) computing an image-quality objective and (b) resolving expensive black-box JPEG constraints.

This branch replaces that loop with a deterministic finite-domain **objective-ranking plus sequential proof-by-rejection** algorithm. There are no GP kernels, independent JPEG-QF assumptions, guessed BER values, PSNR/BER scalarization coefficients or monotone-BER assumptions.

## Mathematical contribution 1 — exact 4x4 SVD-QIM coefficient distortion

Read the pinned original guofei `blind_watermark/bwm_core.py`, commit `322c90dc02d45644692095b34d3a6b735b6edbd8`. In *slow* mode each channel's Haar-LL 4x4 block is DCT-transformed, deterministically shuffled, and decomposed:

`A_b = U_b diag(sigma_b) V_b^T` (NumPy uses `V^T` as `v`).

Let the payload bit assigned to this block *after upstream password_wm shuffle* be `w_b ∈ {0,1}`, and `a_b=1/4+w_b/2`. The upstream first and second singular value quantizers are exactly:

`q_1(s,d) = (floor(s/d)+a_b)*d`

`q_2(s,20) = (floor(s/20)+a_b)*20`.

As long as all other singular values and the original U,V are unchanged, orthogonality gives an **identity**:

```math
||A'_b(d)-A_b||_F^2
 = (q_1(sigma_{b,1},d)-sigma_{b,1})^2
 + (q_2(sigma_{b,2},20)-sigma_{b,2})^2.
```

Shuffling is a permutation, and DCT/IDCT are norm-preserving in exact arithmetic. Therefore the sum of this identity over all 3 color channels and all 4x4 LL blocks gives the exact **transform-domain** squared Frobenius perturbation. Upstream Haar inverse likewise preserves ideal coefficient-space energy before padding crop and subsequent pixel operations.

Consequently `experiments/spectral_certificate_qim.py` precomputes the original shuffled-DCT SVDs **once per image**, then evaluates all 720 integer `d` by a simple vectorized function of their original `sigma_1`. Chunked computation consumes `O(number_of_blocks * chunk_size)` working memory. This is a mathematically grounded deterministic surrogate for the eventual RGB image distortion.

**IMPORTANT:** RGB conversion, image cropping, clipping, uint8 rounding and PNG encoding prevent identifying this transform-domain energy with actual final PNG RGB MSE. It must not be mislabeled as exact RGB PSNR.

## Mathematical contribution 2 — exact original RGB PSNR objective

For *certification of the original research objective*, use `--objective rgb_mse` (the default). Here `experiments/exact_rgb_objective.py` enumerates all 720 candidates through the **original unchanged upstream encoder and OpenCV PNG encoder**, decodes exact uint8 RGB pixels with Pillow and calculates actual original-vs-watermarked RGB MSE.

No smoothness approximation or analytic proxy is involved. The resulting ordered values are exactly the monotone opposite of RGB PNG PSNR for all d1 (fixed RGB peak 255).

This global RGB ranking is more computationally expensive than the fast spectral ranking, but it provides a rigorous reference benchmark and an automatic per-image `d1` selection, unlike fixed hyperparameter BO claims.

`--objective spectral` is a separate faster experimental option that proves optimality only for transform-domain squared energy; its reported RGB PNG PSNR is **not** a globally certified RGB optimum.

## Theorem — finite-domain globally optimal *feasible* solution

Let `D={1,...,720}`, and suppose `J(d)` is evaluated **exactly** for every `d∈D`. Sort all candidates in nondecreasing `(J(d), d)` lexicographic order. Visit this list once. For each candidate:
- Measure clean extraction errors and the required actual JPEG QF errors (early stop is permitted after a **genuinely measured** violation).
- Reject candidate immediately if any measured error is nonzero.
- Accept a candidate ONLY after all nine required JPEG QFs plus clean were actually tested and verified to have **zero** erroneous bits.

**Claim:** The *first* accepted candidate `d*` minimizes `J(d)` over all feasible candidates in `D`.

**Proof:** Every `d` with `(J(d),d)<(J(d*),d*)` appears before `d*` in the list. Because `d*` is the first acceptance, each earlier candidate has a genuine clean or JPEG constraint-violation witness and is infeasible. Any untested candidate is ranked no better than `d*`. Therefore no feasible candidate can have a better objective value (ties resolved by smaller d). QED.

This is a genuine global certificate; a posterior GP prediction is never treated as verification. If a user budget interrupts the ordered search before any verified candidate, return `evaluation_budget_exhausted` **without** an optimum claim. If all 720 are evaluated and rejected, report proven infeasibility for this finite domain and experimental protocol.

For `J(d)=actual PNG RGB MSE`, the theorem **exactly certifies the globally maximum RGB PSNR** over the user-specified 720 steps under the strict zero-BER constraints. For `J(d)=spectral Frobenius energy`, it certifies only the spectral optimum.

## Why constraint-evaluation order can be short-circuited rigorously

Feasibility is the conjunction `clean_success ∧ C_5 ∧ ... ∧ C_95`. One actually measured false condition proves the conjunction false regardless of untested QFs. Hence the upstream `evaluate_d1_early` returns an exact rejection witness and makes it logically unnecessary to run other QFs *for that candidate's feasibility decision*. Nothing is imputed for skipped QFs. This is exact Boolean short-circuiting, not a BER monotonicity heuristic.

It does not by itself establish that QF5-first globally minimizes all *learning* costs. The present theorem deliberately makes no assumptions about that separate, more complex sequential experimental-design problem.

## Metrics, complexity and fairness

- Spectral mode: original per-block SVD preprocessing once, `O(720 * 3 * number_of_blocks)` cheap scalar distortion scoring, plus **only as many JPEG extractions as necessary** to find a feasible candidate in ascending spectral energy.
- Exact RGB mode: `720` complete *PNG embedding* operations plus the necessary ranked **real JPEG extractions**. Its global optimum guarantee has a real runtime price; do **not** describe it as a 36-evaluation BO victory or as faster than legacy V2 without measuring.
- Both modes log 720 score entries, all actual tested candidates, tested QF prefix and bit error counts, JPEG call counts, source hashes, wall time, winning d1, true PNG PSNR and an exported winning PNG.
- The original 36-evaluation V2 is run as an optional matched source-image comparison, with actual PNG PSNR and total wall-clock costs reported. It is a valid low-cost approximation baseline, **not** an exact-global-optimum algorithm.
- Tests check the orthogonal SVD Frobenius identity with nontrivial matrices; strict certificate order; disconnected feasible regions; budget exhaustion; invalid/synthetic claims; and exact encoded RGB pixel parity with the original upstream PNG writer.

## Reproduce with real Pillow JPEG

```bash
python -m pytest -q tests/test_spectral_certificate_qim.py tests/test_exact_rgb_objective.py
python -m experiments.adaptive_d1_public_image_corpus --output-dir /tmp/source-images
# Exact original RGB PSNR global-optimality mode:
python -m experiments.spectral_certificate_qim_pilot \
  --objective rgb_mse --input-dir /tmp/source-images \
  --output-dir /tmp/certificate-results --compare-v2
# Faster exact transform-domain ranking (different objective):
python -m experiments.spectral_certificate_qim_pilot \
  --objective spectral --input-dir /tmp/source-images \
  --output-dir /tmp/spectral-results --compare-v2
```

Dependencies and pinned upstream commit are recorded in `.github/workflows/spectral-certificate-qim.yml`.

### Research integrity and scope

Only validated JPEG results are performance evidence. Unit tests prove invariants, not that the method is better across images. The exact search theorem is about **all 720 fixed integer candidates and the fixed single-image payload/JPEG protocol**, not generalization to unseen image distributions or globally optimal step values outside 1..720. The deployment budget tradeoff must be reported along with the quality gain.

This approach is a mathematically defined **finite search with a global optimality certificate**, not a new Bayesian Optimization acquisition formula. Its scientific strength is correctness and the ability to benchmark all approximate optimizers against an actual per-image optimum rather than tuning arbitrary BO rules against one another.
