# PSO 自適應 QIM 步長：文獻數學模型對照與可驗證實驗方案
日期：2026-11-13
狀態：研究設計；本文件沒有宣稱新增影像實驗或跨影像泛化結果。

## 文獻與證據邊界
1. Zhu & Liu (2009), *An optimal adaptive quantization index modulation watermarking algorithm*, Chinese Optics Letters 7(7), 580–584, DOI: 10.3788/COL20090707.0580, https://opg.optica.org/col/abstract.cfm?uri=col-7-7-580 。**僅可取得摘要，尚未核對正文公式**。已確認 DWT 近似子帶分塊、SVD 奇異值向量 QIM、統計模型結合 PSO 決定各區塊量化步長。不可把下述自行設計的 fitness 當成 Zhu–Liu 原公式。
2. Teoh et al. (2025), *A robust SVD-based watermarking scheme using orthogonal vectors and PSO-enhanced scaling factor*, Cluster Computing 28:850, DOI: 10.1007/s10586-025-05581-w, https://link.springer.com/article/10.1007/s10586-025-05581-w 。公開正文 §3.5、§4.3：PSO 位置是 U/V 向量嵌入 scaling factors，不是 QIM d1；速度更新為 v <- w v + c1(pbest-x)+c2(gbest-x)，位置 x <- x+v；50 particles、150 iterations、w初始1、damping 0.9、c1=1.5、c2=3。Algorithm 4 fitness 以 PSNR >=43 dB 作硬閾值，達標時以 NC_WI 與 extraction similarity 的乘積評估 robustness，否則 NC_W=0。此處是依公開文章的文字化 pseudocode 說明，不是自行推導的精確原始碼。
3. **模型差異**：Zhu–Liu 研究「區塊自適應 QIM 步長」，Teoh 研究「U/V scaling factor + PSO」；本倉庫研究「固定上游 blind_watermark 的單一整數 d1」，不得混稱同一嵌入公式。

## 倉庫已完成的實驗（PR #39）
- reports/ADAPTIVE_D1_GRID_QF5_QF10.md：固定主圖、d2=20、32-bit、Pillow RGB 4:4:4、QF5–10，整數 d1=1…150 的 900 個 BER 量測；40 dB + 六個 QF 全零 BER 的 Model A 不可行；最小全零 BER d1=140，PSNR=28.240 dB。
- Model B: J_0.5=0.5*mean(BER)+0.5*max(0,(40-PSNR)/40)，Grid oracle d1=33、J=0.0442100、mean BER=0.0572917、worst BER=0.3125、PSNR=38.755 dB。
- reports/ADAPTIVE_D1_OPTIMIZER_BENCHMARK.md：24 unique evaluations x 10 seeds：Random mean J 0.0983193 / 0 hits；PSO 0.0855722 / 0 hits；DE 0.0729312 / 3 hits；BO 0.0620455 / 5 hits。此結果來自已量測 Grid lookup oracle，並非每個 optimizer 重新跑 JPEG；其比較只證明這一張圖與這一 objective 的有限預算表現。

## 我們的研究假說：離散多樣性 PSO (Diversity-Preserving Integer PSO, DP-I-PSO)
先保留 Model B 原式，確保與已完成 benchmark 可直接比較。粒子狀態保留連續 x,v，候選 d=clip(round(x),1,150)；每次 fitness 都查實測表或真正 JPEG 評估，不可使用平滑 surrogate 值充當 BER。
- 標準 PSO 基線：沿用現有 experiments/adaptive_d1_optimizer_benchmark.py 的版本與 seeds，確保可比較。
- 候選改良 1：粒子初始化採均勻分層，避免粒子集中。
- 候選改良 2：連續 3 次未改善 global best 時，以預先指定比例（例如 25%）重新初始化最差粒子，保留 elite；避免在跳躍曲線局部停滯。
- 候選改良 3：離散候選去重時，優先從「尚未評估且距離已評估點較遠」的整數挑選，而非純隨機補點；評估數仍嚴格 24。
- 以上三個改良須做消融實驗 (base / +stratified / +restart / +diversity / full)，不得只報 full 最好的一次 seed。
- 為避免在單圖上調參過度擬合，先將現有 150 點 Grid 當作工程測試，正式超參數選擇只用開發集影像，最終固定參數後才測未見影像。

## 第二個候選目標：風險敏感型 PSO（另立實驗，不覆蓋 Model B）
J_risk(d)=lambda*mean_q BER_q(d)+rho*max_q BER_q(d)+(1-lambda-rho)*max(0,(tau-PSNR(d))/tau)，其中 lambda>=0、rho>=0、lambda+rho<=1，tau 預先固定。研究理由：原 Model B 在 d1=33 平均 BER 約 5.73%，但 worst QF BER 31.25%；加入 worst-case penalty 可測試是否改善低 QF 的保守表現。rho 只用開發集挑選，與原 Model B 的 oracle 必須分開重新計算，不可直接比較不同目標函數數值。

## 盲式擷取與「自適應」的部署條件
PSO 的 fitness 在離線設計階段可以使用已知 watermark bits 計算 BER；**正式盲式擷取不可用真值 payload 或原圖**。若每張圖搜尋得到不同 d1，解碼端必須透過明確 side information / metadata 得知 d1，或使用雙方可重現且不依賴原圖的規則。沒有這個機制，只能宣稱「每圖離線自動調參」，不能宣稱「無額外資訊的完整盲式自適應系統」。此外，如果搜尋時使用已知的 QF5–10 攻擊集合，應明示其威脅模型；不能稱為未知攻擊下零成本預測。

## 可重現實驗計畫
1. 讀取 AGENTS.md、PR #39 與現有 benchmark/grid 程式；不改上游 DWT/DCT/SVD/QIM、payload、d2、keys、JPEG codec。
2. 在獨立新模組實作 DP-I-PSO，先用 Grid CSV 的 lookup evaluator 驗證評估計數、seed 決定性、收斂軌跡；測試無重複候選、界限、最佳值單調不增、評估總數 24。
3. 使用 seeds 0–49、每 seed 24 unique evaluations，對 Random、standard PSO、DP-I-PSO variants、DE、BO 做同目標公平比較。報 mean/median/std/final J、oracle hits、regret、95% bootstrap CI，並保存每次提案與接受候選的 traces。這是**在單圖上比較搜尋效率**，不等於跨影像證據。
4. 做 12、24、48 次預算敏感度與 3 種初始化設定，避免只挑一組有利預算。固定同一 objective、codec、payload。
5. 資料集補足至少 50 張**不同來源影像**，記錄授權與 SHA-256；先 30/10/10 split。僅在訓練／驗證圖調 PSO 超參數，最後在未見 10 圖報告 per-image BER、worst BER、PSNR、SSIM、評估成本、oracle regret；不使用跨 split 衍生圖。
6. 另立一組「不以測試 JPEG BER 作搜尋 feedback」的低成本 predictor/規則，與 PSO 離線搜尋明確區分，回答「能否在嵌入前、沒有多次攻擊模擬時自動決定 d1」。
7. 完整記錄負結果，保留 CSV、manifest、圖與程式版本；不得因改良 PSO 未勝 BO 而刪除既有 benchmark。

## 決策準則
只有在固定預算下 DP-I-PSO 在未見影像上的 objective/regret、穩定性或運算成本優於標準 PSO，才可說「改良 PSO 有效」。若仍不如 BO/DE，忠實保留結果；研究價值也可能是指出單變數離散 QIM 最佳化不適合傳統 PSO。
