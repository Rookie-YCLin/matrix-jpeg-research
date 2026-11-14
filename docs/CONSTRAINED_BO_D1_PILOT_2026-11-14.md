# Integer constrained Bayesian optimization of d1: first paired real-JPEG pilot

Date: 2026-11-14. This is a **research prototype**, not a proven improvement or global optimum.

## Scope

- Optimize **one integer variable**, d1 in [36, 720], **d2 = 20** held fixed.
- Maximize measured **embedded PNG PSNR** only among candidates passing **clean BER=0 and all nine measured JPEG QFs** 5, 10, 15, 20, 30, 50, 70, 90, 95 with BER=0.
- Preserve the pinned guofei blind_watermark commit, identical payload, image preparation, keys, Pillow encoding, and extraction as the existing V2/early-rejection experiment.
- Compare under the **same 36 distinct d1 evaluations per image**; separately report JPEG attack counts and wall-clock time.
- No BER monotonicity, no guaranteed feasibility of d1=720, no global optimality claim, no unmeasured QF imputation.

## Model and acquisition

- Model the measured PSNR at **every tested d1**, feasible or not, with GaussianProcessRegressor (Matérn-3/2 kernel, normalized integer domain, fixed prior length scale).
- Model the **joint all-QF feasibility indicator** with GaussianProcessClassifier (Matérn-3/2 kernel) after both labels have been observed. This avoids a false independence assumption among JPEG QFs. For a single observed class, use a simple constant prior probability as a cold-start placeholder, not a calibrated posterior.
- Once any feasible point is found, score every **unmeasured integer** by **expected improvement in PSNR times predicted probability of full feasibility** (EIC). Select the highest scoring candidate.
- When no feasible point has been found, combine feasibility probability with distance from sampled steps, to avoid undefined best-feasible EI.
- Every fifth post-initialization candidate is an explicit max-distance coverage probe. This is a pragmatic guard against disconnected feasible islands, **not** a proof that small islands will be found.
- Initialize at d1=(36,90,150,240,400,720); unlike V2, a failing d1=720 **does not stop** exploration.
- Return only the highest-PSNR **actually verified feasible** tested candidate. If none is verified, return status `no_verified_feasible`.

The fixed GP kernel settings and acquisition strategy are a practical starting point, not yet hyperparameter-validated. GPC probability estimates may be poorly calibrated with <36 samples and a fractured binary feasibility surface. A complete nine-QF real measurement is the only success certificate.

## JPEG cost semantics

Reuse `experiments.early_reject_d1_pilot.evaluate_d1_early`. A rejected d1 is terminated at the **first observed error** and is assigned no BER values at missing QFs. A feasible candidate must complete all nine checks with no errors plus clean extraction. Record `tested_qfs`, `jpeg_attacks`, `full_qf_verification`, measured PSNR and wall time. Use the same early-rejection mechanism for V2, so any differences in candidate decisions are due to the search policy, not a cheaper evaluator.

## Run

Policy tests (synthetic only):

```sh
python -m pytest -q tests/test_constrained_bo_d1.py tests/test_auto_zero_ber.py tests/test_early_reject_policy.py
```

Real JPEG paired experiment (requires the existing research image generator and pinned upstream dependencies):

```sh
python -m experiments.adaptive_d1_public_image_corpus --output-dir /tmp/bo-input
python -m experiments.constrained_bo_d1_pilot --input-dir /tmp/bo-input --output-dir /tmp/bo-results --compare-v2
```

`.github/workflows/constrained-bo-d1-pilot.yml` runs the tests and three-image paired real-JPEG experiments. It retains per-d1, actually measured per-QF, trace, result, and comparison artifacts.

## Literature motivation

- Gardner et al., *Bayesian Optimization with Inequality Constraints* (ICML 2014): expected improvement times probability of feasibility.
- Gelbart et al., *Bayesian Optimization with Unknown Constraints* (2014): unknown feasibility and no incumbent.
- Tran et al., *pBO-2GP-3B* (2018): separate objective and binary-feasibility surrogate models.
- Frazier, *A Tutorial on Bayesian Optimization* (2018): GP posterior and acquisition mechanics.
- Amini et al., *Constrained Bayesian Optimization: A Review* (IEEE Access 2025): model/acquisition/final identification distinction.

**Current evidence level:** implementation plus synthetic logic checks (when verified by CI). Real JPEG performance, feasibility rate, and runtime are **pending job results**. Do not present this as empirical validation before archived real-QF measurements have been inspected.
