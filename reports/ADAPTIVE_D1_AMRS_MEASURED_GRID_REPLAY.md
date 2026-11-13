# AMRS measured-Grid replay: first real JPEG-derived objective comparison

The optimizer was evaluated via **lookup of previously measured** `outputs/adaptive-d1-grid-qf5-qf10-d1-1-150/per_d1.csv` from PR #39. This is **not** a new JPEG run. Fixed parameters: 8 uniform coarse anchors, up to 3 basins, separation=10, explore_every=6, priority penalty=0.12 times observed objective spread times visits/(1+8).

| Budget | Best d1 found | Best Model B objective | Regret to full Grid oracle |
|---|---:|---:|---:|
| 12 | 30 | 0.09246827528457538 | 0.048258232318992886 |
| 24 | **33** | **0.044210042965582494** | **0** |
| 48 | **33** | **0.044210042965582494** | **0** |

Oracle d1=33, J*=0.044210042965582494. This method is deterministic with these settings; 200 repeated seeds would not constitute 200 independent trials. Its first 24 evaluated d1 points were: `10,29,47,66,85,104,122,141,28,30,31,32,27,33,1,34,35,36,37,38,56,39,26,40`.

The 24-query result matches the oracle **on the already-used development image**. It is not evidence for 90% unseen-image hit rate. Compare against the earlier 24-query fixed n=8 nearest method, which also matched the oracle on this image; no superiority claim is warranted. Synthetic-function benchmark reports 78/100 near hits at budget 24 and 98/100 at budget 48.

The calculation was run using JavaScript direct measured-CSV lookup, mirroring `experiments/adaptive_d1_adaptive_regions.py`. The full Python repository implementation has not been tested against real JPEG in this session.

Next: freeze settings, run new independent image Grids, compare paired exact/epsilon hits and wall-clock cost.
