# 單圖離散 d1：簡單搜尋策略的 Grid 回放（2026-11-13）

## 資料與方法
使用 PR #39 的固定主圖、整數 d1=1..150 的**既有實測** `model_b_lambda_0_5` 值，Grid oracle 為 d1=33、J=0.044210042965582494。此研究不重跑 JPEG，不產生新的 BER 或 PSNR。以固定 LCG seed=123，對每種方法／預算各 200 次試驗，全部候選不重複計數。

方法：
- random：無放回隨機取整數；
- stratified：將 1..150 分層後每層隨機抽樣；
- coarse_refine：先均勻取最多 10 個粗點，接著反覆在當前 best d1 附近 7 個未測候選中隨機抽取。這個策略有強烈的「鄰近好點附近可能還有更好點」歸納偏差。

## 初次回放結果
| 方法 | 評估預算 | 200 次 mean final J | Grid oracle 命中 |
|---|---:|---:|---:|
| Random | 12 | 0.10736773 | 24/200 |
| Random | 24 | 0.08548797 | 32/200 |
| Random | 48 | 0.06637013 | 61/200 |
| Stratified | 12 | 0.10175920 | 16/200 |
| Stratified | 24 | 0.08273688 | 36/200 |
| Stratified | 48 | 0.06840766 | 61/200 |
| Coarse + refine | 12 | 0.11776042 | 0/200 |
| Coarse + refine | 24 | 0.08537177 | 56/200 |
| Coarse + refine | 48 | **0.04468067** | **187/200** |

## 解釋與限制
1. 48 次預算下 coarse_refine 在**這一張圖**有優勢，但 12 次預算反而比 Random 差；這是預算依賴現象。
2. 此方法可能因為 d1=33 恰好落在 coarse 初始化附近、局部結構較有利而占優；不能由此推論跨影像優勢，也不能直接與 PR #39 的 BO/DE 24 次、10 seeds 結果比較。
3. 需要在同一套 200 seeds/預算/目標函數下重跑 BO、DE、PSO 與 coarse_refine，並用未見影像驗證。
4. 結果是 JavaScript 直接讀取 GitHub CSV 後的實際 Grid lookup 計算；`experiments/adaptive_d1_simple_replay.py` 是可重現的 Python 對應實作，應在完整倉庫環境執行核對輸出。未聲稱已在 GitHub Actions 或 Python runtime 成功執行。
5. 對每個候選做一次真正的 JPEG 評估成本遠高於查表；實際部署仍須獨立測量 wall time。

## 下一步
- 先核對 Python replay 與上述數字完全一致；
- 同預算比較 BO/DE/PSO（不只比 random）；
- 對 coarse_refine 的 coarse 點數與鄰域大小做預登記消融，避免只挑單圖最好的設定；
- 跨圖 30/10/10 split 後再決定主方法。
