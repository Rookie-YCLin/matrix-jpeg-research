# 自適應 `d1` 最佳化：第一階段架構與可行性盤點

日期：2026-11-13  
狀態：**已驗證的程式架構盤點；尚未執行任何新的參數搜尋或核心程式修改。**

## 結論摘要

針對「每張圖自適應選擇第一奇異值 QIM 步長 `d1`」這個新問題，現有專案可用，而且不必先改動上游核心。`d1` 已是 `WaterMark.bwm_core` 的執行期屬性；讓嵌入端與盲式擷取端使用同一整數 `d1` 即可完成一次候選評估。第一輪會固定 `d2=20`、payload、金鑰、DWT/DCT/SVD、JPEG 編碼器與判決方式，只搜索 `d1∈{1,…,150}`。

這不是連續、保證單調的最佳化問題。QIM 的 floor／mod 判決、JPEG、像素裁切、三通道與跨區塊平均、最後的 1-D K-means 都使 BER 對 `d1` 成為離散且可能跳變的黑盒函數。因此 Grid、Random、PSO、Differential Evolution（DE）與 Bayesian Optimization（BO）都可以做**有限預算的比較**，但不能預先假定「步長越大 BER 越低」或用二分搜尋代替實測。

現有資料不足以訓練或公平測試 30/10/10 的影像特徵預測器：版本庫只有 `data/ascent.png`，先前使用者提供的 `C:\Users\macuz\OneDrive\圖片\Test` 有 10 張獨立 JPEG。即使全部可讀，也至多 11 張，少於所需 50 張；不得藉由裁切、重複 JPEG 品質或重複訓練來充數。下一階段可先在固定主圖完成搜尋器的工程驗證；建立泛化預測器前須新增具有可再散布來源、授權與 manifest 的至少 50 張不同影像（例如公開影像資料集的固定子集）。

## 已盤點的處理鏈

固定上游版本為 `guofei9987/blind_watermark` commit `322c90dc02d45644692095b34d3a6b735b6edbd8`。實作採 RGB 輸入後的 DWT，將近似子帶分割為 4×4 區塊；每個區塊經 DCT、由 `password_img=1` 決定的置換、完整 SVD，再逆向重建。現有正式圖是上游 `ori_img.jpeg`（RGB `1108×738`）、32-bit payload `10110010111001000101101011010001`、兩把金鑰皆為 1。

在上游 `bwm_core.py`，慢速完整 SVD 路徑的單區塊嵌入為

\[
\sigma'_1=d_1\left(\lfloor\sigma_1/d_1\rfloor+1/4+b/2\right),\qquad
\sigma'_2=d_2\left(\lfloor\sigma_2/d_2\rfloor+1/4+b/2\right).
\]

擷取端第一票是 `1[σ1 mod d1 > d1/2]`；第二票是 `1[σ2 mod d2 > d2/2]`；當 `d2>0` 時以 `3:1` 融合。所有重複區塊與三個通道對同一 payload 位置平均，再由 1-D K-means 給出公開 bit API 的 32 個 bit。故本研究只改 `d1` 時，`d2=20` 與所有其他步驟仍固定；正確 payload 僅可在最後計算 BER，不可進入盲式解碼。

現有 `experiments/ori_qf_scan.py` 已固定 Pillow JPEG：RGB、`subsampling=0`、`optimize=False`、`progressive=False`；目前品質清單是 `5,10,…,95`。`experiments/svd_qim_sweep.py` 已證明可藉由

```python
wm.bwm_core.d1, wm.bwm_core.d2 = d1, d2
```

建立同步的嵌入／擷取實例。`experiments/svd_qim_psnr.py` 已有 float64 RGB MSE/PSNR 實作。當前 requirements 不含 scikit-learn、Optuna、PSO 或 BO 套件；後續應先以小型、可審計的 NumPy 實作或明確鎖定新增套件，不能不記版本地依賴環境中的套件。

## 已知基線與資料狀況

正式主圖的封存基線是 `d1=36,d2=20`：QF5 為 12/32、QF10 為 1/32、QF15 和 QF20 為 32/32、QF25–95 為 0/32。G6 `(90,20)` 在 QF15 改為 0/32，但 QF5 變為 32/32。這些結果證實 BER 非單調，卻**不是**新模型 A 或 B 的搜尋結果。

本任務要求的 QF5、6、7、8、9、10 中，QF6–9 尚無封存量測；因此任何宣稱「QF5–10 BER=0」的模型目前均為未驗證。現有 32-bit payload 令單張單 QF BER 的解析度是 `1/32=0.03125`，應同時報告 `errors/32`，不把小數 BER 誤作連續且精細的訊號。

現有私人外部資料夾含 10 張圖，像素範圍約 `1024×676` 至 `3000×2000`。它們可在使用者已允許的本機驗證中使用，但沒有隨版本庫保存的來源、授權或 split manifest，不能當作可發表的 50 圖訓練／測試集。正式資料集尚缺 **至少 39 張**獨立影像，實務上應先建立不重疊的 50 張公開清單與 SHA-256，再固定 train/validation/test split。

## 模型 A：可行性優先的最小步長

對圖像 `I` 與候選整數 `d`，令 `e_q(I,d)` 是在 QF `q` 的錯誤 bit 數，`B_q=e_q/32`；令 `P(I,d)` 是攻擊前標記 PNG 相對原圖的 RGB PSNR。令

\[
\mathcal Q=\{5,6,7,8,9,10\},\qquad \tau=40\;\mathrm{dB}.
\]

模型 A 是字典序問題：

\[
d_A^*(I)=\min\{d\in\{1,\ldots,150\}:\max_{q\in\mathcal Q} e_q(I,d)=0\ \land\ P(I,d)\ge\tau\}.
\]

先檢查 BER=0 和 PSNR 門檻，然後才選最小 `d`；它沒有把 PSNR 與 BER 任意相加。若集合為空，結果必須明列為 **infeasible（在 1–150、此圖、此 payload、此 codec 與 40 dB 門檻下）**，而不是外推出「演算法失敗」或偷偷放寬條件。`τ` 會寫入 config，且可事前改成另一個值再重跑，不能看結果後逐圖改門檻。

## 模型 B：固定權重的折衷目標

為比較在沒有可行解時如何折衷，定義平均 BER 與最壞 BER：

\[
\bar B(I,d)=\frac1{6}\sum_{q\in\mathcal Q}B_q(I,d),\qquad
B_{\max}(I,d)=\max_{q\in\mathcal Q}B_q(I,d).
\]

以 40 dB 為品質尺度，非負的正規化失真為

\[
D(I,d)=\max\{0,(\tau-P(I,d))/\tau\}.
\]

在預先指定 `λ∈[0,1]` 下，模型 B 最小化

\[
J_\lambda(I,d)=\lambda\bar B(I,d)+(1-\lambda)D(I,d).
\]

每次結果同時報告 `\bar B`、`B_max`、六個 `e_q/32`、PSNR 及 `Jλ`。`B_max` 不納入此基本式並非忽略風險，而是避免同時把同一 BER 懲罰兩次；它是必要的安全報告欄位。後續可另行預登記 min-max 版本，但不能把其結果與本模型混稱同一目標。

## 搜尋法的公平比較設計

每一次候選評估都必須完整執行嵌入、無攻擊 PNG PSNR、QF5–10 六次 JPEG、盲式擷取與計分。建立快取鍵 `(image SHA-256,d1,QF,codec settings,payload,keys,upstream commit)`，避免重複量測被誤算成新的函數評估。所有方法共用同一整數域、同一初始候選（若適用）、相同獨立評估預算與相同 benchmark 圖；Grid 的預算不足掃描 150 點時，須事先說明其子網格，不能事後挑點。

| 方法 | 本問題的可行性 | 公平實作要點 |
|---|---|---|
| Grid | 是；150 個點可作真值基準 | 完整枚舉 1–150；同時產生 BER/PSNR/Pareto 曲線。 |
| Random | 是 | 固定多個 seeds、無放回抽樣，與其他法同一評估數。 |
| PSO | 是，但位置須投影到整數 | 每次更新後 clip 到 1–150、round、快取去重；重複點不消耗新的有效評估。 |
| DE | 是，但需離散化 | 浮點變異後同樣 clip/round；固定 mutation/crossover 與 seed。 |
| BO | 是，但樣本很小且目標跳變 | 以已評估整數點為候選集合；需明記 surrogate、acquisition、初始設計與 random tie-break。 |

Grid 才能在單張圖 1–150 範圍內確定 `d_A^*`、`d_B^*` 和 Pareto 前緣；PSO/DE/BO/Random 的角色是比較「在較小預算內逼近 Grid 真值的速度與穩定性」，不是在 Grid 已跑完後聲稱找到更好的未知解。每種隨機方法至少多個固定 seeds，輸出評估數、牆鐘時間、最佳值軌跡與命中 Grid 最佳解的比例。這也處理了 objective 可能平臺、反轉及多個同分 `d1` 的情形。

## 特徵式自適應規則：可做，但目前尚未有訓練資料

針對每張**未見**圖，只能從原圖（以及若預先允許的無水印 JPEG 預分析）計算下列特徵；解碼時不可使用原圖、真實 payload 或 BER。

1. 灰階平均、變異數與分位數；
2. Sobel 梯度均值／變異數、局部熵或紋理能量；
3. Haar DWT 的 LL/LH/HL/HH 相對能量；
4. 4×4 DCT 的低頻與高頻能量比例；
5. 區塊 DCT-SVD 的 `σ1`、`σ2` 分布、`σ1/σ2`、譜衰減／有效秩；
6. 若採用：在固定 QF 的未標記 JPEG 預分析差異，並把 QF 視為已知部署條件而非由測試答案反推。

訓練標籤不是人工指定 `d1`，而是每張訓練影像的 Grid 模型 A 結果；若 A infeasible，可用模型 B 的固定 `λ` 最優值並保留 infeasible 標記。先使用可解釋基線（最近鄰或正則化線性／樹模型）預測整數 `d1`，再用 validation 選模型與超參數，最後僅在完全未見的 test 影像一次報告 BER、PSNR、infeasible rate、相對 Grid oracle regret 與最壞 QF BER。深度學習或 deep unfolding 以目前 50 張資料量不合適；若未來有大量含標籤影像，可把 QIM 的 round/mod 以 straight-through estimator 或軟量化近似，但仍必須用真正的盲式 JPEG 評估驗證。

## 風險、修正與下一步

- **已驗證：** `d1` 可不改核心地同步設定；JPEG 與 PSNR 計算已有可重用基礎；BER 對 QF／步長不應視為單調。
- **初步支持：** Grid、Random、PSO、DE、BO 可以在固定離散域做公平的黑盒比較；其效果仍待實測。
- **未驗證：** QF5–10 是否有任何 `d1≤150` 同時達成零 BER 和 40 dB；各搜尋法是否能在小預算穩定逼近 Grid；影像特徵是否能預測最佳 `d1`。
- **資料不足：** 50 張 train/validation/test 所需影像尚缺至少 39 張，且現有本機圖沒有版本化資料清單。

下一階段只新增一個獨立實驗模組與 outputs 目錄：先以 Grid 對固定主圖跑 QF5–10、`d1=1…150`，寫入 config JSON、逐影像 CSV、manifest、SVG（BER–d1、PSNR–d1、Pareto）與完整 markdown；依此如實判定模型 A 的可行／不可行和模型 B 的基線。未得到這份 Grid 真值前，不執行或宣稱 PSO／DE／BO 的優劣，也不改寫上游核心。
