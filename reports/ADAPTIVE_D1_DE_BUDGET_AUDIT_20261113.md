# 2026-11-13：DE 評估預算審計與公平回放

## 發現：原 DE benchmark 有資訊洩漏
`experiments/adaptive_d1_optimizer_benchmark.py` 的 `de_method` 在每輪先查 `oracle[candidate]["model_b_lambda_0_5"]` 決定是否接受 trial，但只有之後外層 `proposed.append(d)` 才算一次有效評估。因此一個候選可能在未計費情況下已經使用真實 objective；其後續比較的 24 次有效評估預算不公平。既有 PR #39 報告 DE 3/10 命中不能直接用來宣稱 DE 的公平優勢。此報告不修改原始歷史紀錄。

## 公平 DE 設計
每次 `objective(candidate)` 只能透過 `evaluate_unique` 呼叫；呼叫時立即將整數 d 加入已評估集合並消耗一次預算，包含被拒絕的 trial。已查詢候選不得再收費，若產生重複 d，從剩餘整數隨機補點。初始化族群 8 個，後續每個新 trial 依 fitness 與對應族群成員比較，較佳才替換。完整軌跡應保留提案、實測、接受／拒絕與 budget 計數。

## 實際重新回放
透過 GitHub 讀取 PR #39 150 個**既有 JPEG 實測** Model B objective，使用 JavaScript 執行 200 個固定種子（seed 0..199）、12/24/48 次**不重複 objective 查詢**。這是 Grid lookup replay，不是新的 JPEG 實驗。隨機數使用 LCG state=(1664525*state+1013904223) mod 2^32、初始 state=seed+12345。DE 使用 8 人族群、F=0.8、CR=0.9、clip/round 整數。與先前 PR #40 的 LCG seed=123 串流不同，不可直接把兩輪數字混稱相同設定。

| 方法 | 預算 | 200 次平均最終 J | 命中 d1=33 |
|---|---:|---:|---:|
| Random | 12 | 0.10167641 | 25/200 |
| Fair DE | 12 | 0.10722136 | 18/200 |
| Coarse+refine | 12 | 0.11807292 | 0/200 |
| Random | 24 | 0.08295308 | 46/200 |
| Fair DE | 24 | 0.08167139 | 36/200 |
| Coarse+refine | 24 | 0.08590476 | 52/200 |
| Random | 48 | 0.06759637 | 65/200 |
| Fair DE | 48 | 0.06164239 | 80/200 |
| Coarse+refine | 48 | **0.04427956** | **185/200** |

Grid oracle: d1=33、J=0.044210042965582494。

## 判讀
- 在這一張圖的 24 次預算下，公平 DE 與 Random 的平均 objective 非常接近，不能由此宣稱 DE 普遍較優。
- 48 次預算下 coarse+refine 表現強，但 12 次預算下較差；該方法利用目標函數在 d1=33 周圍的局部結構，可能過度適配此圖。
- **原 PR #39 BO 與 PSO 程式仍待獨立審計**。目前不將 BO 5/10 hits 與本輪 200 seeds 數字直接比較。
- 請在完整 Python 環境核對本輪 JavaScript 回放結果，並補充每次 trial 的完整 trace、信賴區間、未見影像結果。

## 下一步
1. 修正 benchmark 的 DE trial 評估計數；檢查 PSO 的 `global_pos` 更新與 duplicate fallback，BO 的初始化和 Gaussian-process kernel 數值穩定性。
2. 在統一 seed、budget、objective 下重新跑 BO、DE、PSO、Random、coarse+refine。
3. 跨影像驗證前不得定論何種方法最好。
