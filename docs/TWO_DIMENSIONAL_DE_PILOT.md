# Two-dimensional integer DE pilot (d1, d2)

## Scope
Use SciPy's established differential_evolution, **one optimization method only**, to select two integer QIM steps in guofei's normal-mode SVD embedding:
- d1 controls singular value s[0]; d2 controls s[1].
- Upstream baseline is (36, 20).
- fast_mode bypasses d2 and MUST be disabled.
- Objective: maximize PNG PSNR, with clean BER=0 and all nine JPEG QF BER=0.
- QFs: 5, 10, 15, 20, 30, 50, 70, 90, 95.
- d1 bounds default [36,720] from the previous 1D study.
- d2 bounds [1,120] are **pilot bounds only**, not a claimed optimal or upstream range. Revisit using measured evidence.

## Current implementation
`research/two_dimensional_de.py` provides an isolated callback-driven integer DE search.
It uses SciPy integrality constraints, per-QF nonlinear BER constraints, and memoization
to prevent repeated full evaluation of identical (d1,d2) pairs.

**Evaluator contract**: `evaluator(d1, d2, qfs) -> Measurement(psnr, clean_ber, jpeg_ber)`.
It must actually embed, PNG-score, and decode all QFs for the same image/payload/keys.
Incomplete evaluations are rejected. No JPEG attack is simulated by the optimizer.

## What is not done
- The callback has NOT been connected to the existing watermark/JPEG evaluator.
- No real-image DE run has been performed or verified.
- No claim of superiority to V2 or a global optimum is justified yet.
- Strict feasibility may be rare; SciPy can return an infeasible candidate. Check
  `SearchResult.feasible` before reporting a usable result.

## Next integration and scientific evaluation
1. Connect a fresh per-pair watermark embed/extract evaluation with explicit d2.
   Ensure the original upstream normal-mode code actually consumes both steps.
2. Confirm the 36/20 baseline matches prior results and clean/JPEG BER decoding.
3. Test synthetic contracts; run a small real-image smoke test with a low budget.
4. Evaluate several images and random seeds, tracking best **verified feasible**
   PNG PSNR, unique pairs, actual JPEG operations, wall time and seed variance.
5. Compare to fixed-d2 V2 under matched costs. Exhaustive 2D search is not
   assumed feasible; do not claim a global optimum without proof.

## Reference
- SciPy: https://github.com/scipy/scipy/blob/main/scipy/optimize/_differentialevolution.py
- Upstream: https://github.com/guofei9987/blind_watermark/blob/master/blind_watermark/bwm_core.py
