# JPEG QF early rejection: observed cost reduction, not a new optimizer

Date: 2026-11-14. Origin: the same independent V2 image-dependent zero-BER search; existing selection policy is unchanged. Parent V2 PR: https://github.com/Rookie-YCLin/matrix-jpeg-research/pull/43 . Negative DIRECTGO comparator: https://github.com/Rookie-YCLin/matrix-jpeg-research/pull/44 .

## The experiment

For every unique candidate d1, evaluate clean extraction and then JPEG QFs in frozen order {5,10,15,20,30,50,70,90,95}, stopping after the first BER>0 or a preexisting clean-extraction error. If no failure occurs, all nine QFs have been measured. A candidate is **feasible** only if clean_errors=0 and **every one of the nine actual JPEG tests was performed and produced BER=0**. Untested QFs remain unknown; the CSV logs only actual attacks. The selector still uses one observed positive BER only as a *rejection witness*; its size is not interpreted as the true worst-QF BER.

This approach changes the expense of testing **a candidate**, not how V2 chooses the next d1. The V2 policy uses only feasibility and measured PNG PSNR, hence its d1 sequence should match the full-QF V2 when all observations are deterministic.

## Data-backed counterfactual (historical DIRECTGO trial)

From DIRECTGO experiment https://github.com/Rookie-YCLin/matrix-jpeg-research/actions/runs/43500681849, full per_qf.csv artifacts were checked:

| image | Full JPEG checks | Infeasible d1 candidates | All those failing QF5? | Rejection-first projected checks |
| --- | ---: | ---: | --- | ---: |
| astronaut | 324 | 9 | yes (9/9) | 252 |
| chelsea | 324 | 7 | yes (7/7) | 268 |
| coffee | 324 | 8 | yes (8/8) | 260 |
| **total** | **972** | **24** | **24/24** | **780** |

Projected check reduction 192/972 = **19.75%** for the *same DIRECTGO candidate list*. This is **not** a measured runtime speedup, not the V2 candidate trace, and does not establish QF5 as always the hardest compression setting across all images/steps.

## Actual real-JPEG pilot

Workflow `.github/workflows/early-reject-d1-pilot.yml` applies the unchanged V2 selector with the new streaming QF evaluator on astronaut, chelsea, coffee using identical pinned watermark, JPEG, extraction, image and payload configuration.

The workflow archives:
- `per_qf.csv` only for **actually tested** QFs.
- `per_d1.csv` with the observed BER, checked/skipped QFs and full-verification status.
- `trace.csv` candidate order and cost.
- `result.json` PNG PSNR, best tested d1, total JPEG attacks, elapsed wall time and complete-9-QF baseline count.

Do not claim success or savings until the run has completed and artifacts have been read. Compare candidate sequence, selected d1 and PNG PSNR against V2's verified output, and compare **actual JPEG attack count** (not just d1 evaluations) and wall time separately.

## Design constraints

- Clean extraction remains mandatory, and a failed QF is sufficient to reject.
- Never assign BER=0, BER=1, or an interpolated estimate to an untested QF.
- Early rejection is safe for the binary *all-conditions-feasible* constraint; it cannot produce a complete BER curve for discarded candidates.
- Recheck all nine QFs for the final selected feasible step; current streaming design already does this because all successful QFs are evaluated to completion.
- No global optimality guarantee; images are screened with verified d1=720 eligible anchor.
- This pilot keeps the QF order fixed; future work may optimize QF ordering only using previously observed data, with independent validation.
