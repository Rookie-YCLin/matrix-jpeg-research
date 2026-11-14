# Exact SVD-QIM d1 certificates: archived real JPEG results (2026-11-14)

**Evidence:** [GitHub Actions run 43587204161](https://github.com/Rookie-YCLin/matrix-jpeg-research/actions/runs/43587204161) completed with all jobs successful. Actual candidate and QF traces are retained in downloadable Actions artifacts `certificate-coffee` (ID `14111290489`) and `certificate-moon` (ID `14111070730`). Mathematical policy test: **16 passed**. Pinned upstream PNG pixel parity jobs also passed.

## Fixed protocol (unchanged original watermark and JPEG attack)

- Pinned guofei `blind_watermark` commit `322c90dc02d45644692095b34d3a6b735b6edbd8`.
- Image-specific integer `d1=1,...,720`, `d2=20`, fixed 32-bit payload and keys.
- Full real JPEG zero-BER feasibility across QFs `(5,10,15,20,30,50,70,90,95)`, plus clean.
- Optimize **exact original 8-bit PNG RGB MSE** (hence maximum RGB PSNR). All 720 scores computed by the unchanged upstream embed + OpenCV PNG/Pillow decode. Candidate order is increasing actual RGB MSE; sequential JPEG tests short-circuit at a *measured* failed QF.
- First fully verified candidate must be a global optimum for this **fixed image, finite domain and attack set**; no GP or monotonicity hypothesis.
- Comparison to historical legacy V2 uses the identical source image, same payload and attack settings, but V2 limits itself to 36 candidate evaluations. These are therefore different computational budgets.

## Primary measured results

| Image | Exact best d1 | Exact best PNG PSNR dB | Legacy V2 d1 | Legacy PNG PSNR dB | Gain dB | 720 exact scores? | Expensive candidate checks | Actual JPEG checks | Exact full seconds | Legacy V2 seconds |
|---|---:|---:|---:|---:|---:|---|---:|---:|---:|---:|
| coffee | 96 | 31.049473742154028 | 96 | 31.049473742154028 | 0.000000000 | yes | 96 | 110 | 234.797806670 | 30.411367272 |
| moon | 133 | 24.552893898073723 | 156 | 23.240875873712250 | **+1.312018024** | yes | 128 | 137 | 367.124107905 | 44.716117562 |

Scoring all 720 PNG images took **177.694677259 seconds on coffee** and **259.046311275 seconds on moon**, respectively. These times are included in the exact total seconds above. The exact method **does not claim** to be faster or use the same candidate evaluation budget as the 36-evaluation V2; its new result is a genuine optimality certificate on the complete candidate domain.

## Independent archive audit of both certificates

We downloaded each workflow artifact ZIP and verified:
1. `all_720_ranked_objectives.csv` has **720 unique d1 entries**, exactly `1,...,720`, in nondecreasing actual PNG RGB MSE order.
2. `per_d1.csv` follows **exactly the first N entries** of the globally ranked table, with `N=96` (coffee) and `N=128` (moon). No hidden/skipped higher-quality candidate.
3. The first `N-1` entries are all marked as not fully feasible due to actual constraint measurements. The N-th is fully verified feasible.
4. The final candidate has **9 of 9 real JPEG QF evaluations with zero erroneous bits** and a valid clean extraction.
5. All QF row counts match the manifest `110` for coffee and `137` for moon; **untested QFs remain absent**.
6. `selected_marked.png` has SHA256 equal to `result.json`'s reported `marked_sha256`. The printed metadata and exact PNG PSNR align.

## Scientific inference and limitations

The **theorem** guarantees a globally optimal measured *PNG RGB PSNR*, subject to the fixed zero-BER hard constraints and finite `d1=1..720` domain. It does **not** guarantee maximal resilience to untested attack formats, unspecified JPEG qualities, other payloads/images, or best throughput. The two example images are reused development images, so these are transparent correctness/benchmark experiments, **not** an independent-image generalization study.

The separate `--objective spectral` fast mode ranks exact SVD Frobenius distortion `Σ[(Δσ1(d1))²+(Δσ2(20))²]`. Its proof concerns **transform-domain error only**, not PNG RGB PSNR. Its candidate winner cannot be assumed RGB-global without running the full exact RGB mode.

The promising research direction is now precise: the exact RGB solver provides a provable per-image **reference optimum**, while future faster adaptive algorithms can be evaluated by their *regret relative to that real optimum per unit runtime*, rather than modifying arbitrary BO acquisition penalties and selectively reporting favorable trials.
