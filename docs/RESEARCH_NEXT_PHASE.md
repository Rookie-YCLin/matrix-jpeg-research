# 研究交接：G6 已完成，下一階段僅 PSNR 與矩陣理論（2026-11-08）

> **最新且優先的主持人決策。** 若本倉庫較早的 README、AGENTS、PROJECT_SPEC 或交接文件仍寫「無須 PSNR／尚無成功改良／應繼續搜尋候選」，以本文件為準；那些敘述是歷史階段記錄，不是當前任務。請保留歷史證據，不要回寫假資料。

## 一、研究定位（已定案，不再擴張）

以 guofei9987/blind_watermark 的**原版 SVD-QIM**為基礎，研究**只調整第一奇異值的 QIM 量化步長 d1**，如何影響固定圖片、固定 32-bit 浮水印在 JPEG QF15 的 BER 與 PSNR。這是一個受控的矩陣理論＋工程 trade-off 專題，**不是量化步長全域最佳化**。

- 原版：(d1,d2)=(36,20)；改良版 G6：(90,20)。**d2 固定 20**；DWT、DCT、RGB 通道、金鑰、位元重複嵌入、多區塊融合、K-means、JPEG 編碼設定等不改。
- 唯一圖片：上游 examples/pic/ori_img.jpeg（1108×738；Git blob ef48a056b3cab1d2c08723c014d8d515963f5a07；SHA-256 17bed8cfeb5534351d2f35d4addd9407e0c0132132444276a0f826c7ae9923c2）。圖片本來是 JPEG，計算 PSNR 時需說明基準為其解碼 RGB 像素。
- 正式 payload：10110010111001000101101011010001（**原始 32 bits，不是 ASCII 文字**），固定 password_img=password_wm=1。
- pinned upstream commit：322c90dc02d45644692095b34d3a6b735b6edbd8；使用 full SVD / fast_mode=False。
- JPEG：Pillow、4:4:4、subsampling=0、optimize=False、progressive=False，沿用現有實驗程式的固定條件；不可偷偷改測試管線。
- **主條件 QF15**。既有 BER 曲線範圍 QF5,10,...,95；報告的正向結論可聚焦 **QF15～95 每隔 5 點**。**不追加所有整數 QF16–94 的驗證**，也**不研究 QF<15 的失效原因**；原本 QF5、QF10 的實測資料仍要如實保存／必要時於限制或附錄說明。
- 不新增第二張圖片、不新增 payload 長度掃描、不研究 d2 最佳化、不做無限候選搜尋、不提出「(90,20) 全域最優」宣稱。已有 15 組候選探索，明示 (90,20) 是有限候選中選定的**單參數簡化方案**，並非純理論預測。

## 二、已完成且已提交 main 的結果（不要重新發明或重跑完整 G6）

| JPEG QF | 原版 (36,20) | G6 (90,20) |
|---|---:|---:|
| 5 | 12/32，BER=37.5% | 32/32，BER=100%（已知限制） |
| 10 | 1/32，BER=3.125% | 0/32，BER=0% |
| **15** | **32/32，BER=100%** | **0/32，BER=0%** |
| 20 | 32/32，BER=100% | 0/32，BER=0% |
| 25,30,...,95 | 每點 0/32 | 每點 0/32 |

- 原版 QF15、QF20 的 32 bits 全部互補；G6 QF5 也是全部互補。**「完全反相」是觀察事實，確切機制未證明**；不能無證據歸咎於 K-means 標籤交換或單一奇異值跨界。
- 曾額外驗證兩組不同 32-bit payload，在 QF10、15、20、25 改良版均 0/32；正式主線仍固定原 payload。
- 證據（已存在）：
  - [G6 方法與限制](../reports/G6_SVD_QIM_QF15_SUCCESS.md)
  - [配對 BER CSV](../outputs/svd-qim-qf15-selected/results.csv)、[manifest](../outputs/svd-qim-qf15-selected/manifest.json)
  - [15 組歷史候選完整 CSV](../outputs/svd-qim-qf15-exploration/results.csv)
  - [最小上游 patch](../patches/bwm_core_svd_d1_90.patch)
  - [固定驗證腳本](../experiments/svd_qim_validation.py)、[候選探索腳本](../experiments/svd_qim_sweep.py)
  - [成功 CI](https://github.com/Rookie-YCLin/matrix-jpeg-research/actions/runs/42463429539)

## 三、剩餘工作 A：PSNR，僅為呈現 Trade-off

**問：為了讓同一張圖在 QF15 的 BER 從 100%→0%，像素品質有多少差異？** 只比較 (36,20) 與 (90,20)，不要重新搜尋參數。

請報告兩種清楚區分的 PSNR：
1. **主要：QF15 後**。原圖 JPEG 解碼後的 RGB 像素 I，與各自嵌入（無損 PNG 中介）並用固定 Pillow QF15 存成 JPEG、再解碼後的 RGB 圖 J15，計算 PSNR(I,J15)。這是「最終經攻擊影像」相對原圖的畫質。
2. **輔助：嵌入後壓縮前**。I vs 各自無損嵌入 PNG 的 RGB 像素 W，計算 PSNR(I,W)。這有助區分嵌入失真與「含 JPEG 的最終失真」，但兩種 PSNR 不得相減當作可加的物理失真成分。

RGB 8-bit、逐像素 3 通道，使用 float64 計算：
MSE = sum((I-J)^2) / (3 * H * W)；
PSNR_dB = 10 log10(255^2/MSE)，MSE=0 時為 +inf。
必須校驗圖片尺寸與通道、避免 uint8 減法溢位；確保同一基準原圖、同一 JPEG 設定與 payload、金鑰。輸出四個 PSNR 值、兩個 paired Delta=PSNR_G6−PSNR_original、MSE、SHA256、版本與可重現命令；PSNR 結果為**待測**，不得捏造或預設改良版必定較差。可補一張簡單對照表，不增加其他圖、攻擊與候選搜尋。

## 四、剩餘工作 B：有脈絡的矩陣理論推導

目標是教授能讀懂的 **「定理 → 假設 → 推論 → 實驗對應 → 限制」**，不是用定理假裝精確預測 BER=100%→0%。

核心：
1. 定義 SVD：A=UΣV^T，奇異值 σ1≥σ2≥...≥0，原版只修改前兩項。
2. **明確標示是 guofei 原版就有的 SVD-QIM**，不是本研究發明。嵌入公式 σ'_i=d_i(floor(σ_i/d_i)+1/4+b/2)；b=0 時格點 d/4，b=1 時 3d/4；用模 d 的局部判決，理想裕度 m_i=d_i/4；原版 d1=36→m1=9，改良版 d1=90→m1=22.5（2.5 倍）。
3. JPEG 前後，在**相同變換域及對應區塊**定義有效擾動 E：A_attacked=A_watermarked+E；|σ_i(A+E)−σ_i(A)|≤||E||_2。若嵌入後奇異值恰在理想格點、索引與局部判決相容，||E||_2<d_i/4 可作**局部充分條件**，**不代表真實 JPEG 滿足此界**，也不保證跨區塊分數與 K-means 最終 BER。
4. SVD 正交不變性給出 ||A'−A||_F^2=(Δσ1)^2+(Δσ2)^2。原版 QIM 可推 |Δσ_i|≤3d_i/4，故 ||A'−A||_F≤(3/4)sqrt(d1^2+d2^2)。這是**局部變換域的保守最壞上界**，不是整圖 PSNR 的確定值，也不能說「d1 越大實測失真必然越大」。
5. 整張 RGB 影像 MSE=||I−J||_F²/(3HW)，PSNR=10 log10(255²/MSE)；說明映射至像素域時有 DWT/DCT 逆變換、裁切、取整、JPEG 重量化等環節，兩個域不能直接等號替換。
6. 分辨書中正式定理、從定理推導的式子、本研究 QIM 公式與實測結果；避免把條件式寫成必然保證。真實 32/32 全反相機制仍是未解限制，不強制延伸到 QF<15。

參考文獻：Dennis S. Bernstein, *Matrix Mathematics: Theory, Facts, and Formulas*, 2nd ed., Princeton University Press, 2009。優先核對原書印刷頁碼：
- §5.6, pp.301–303：SVD 定義與 **Theorem 5.6.4**。
- §9.2, pp.546–549：矩陣／Frobenius 範數。
- §9.6, p.562：**Proposition 9.6.8** 的奇異值加法不等式，可導出前述 Weyl 型擾動界。
檢核實際頁碼與命題精確條件；此書**不是 JPEG、QIM 或 PSNR 的直接來源**。不要把全書 PDF 上傳公開倉庫，不要大段轉載受版權保護內容；僅用公式、自己的證明與正式書目引用。

## 五、代理交接與分工

- [Codex 任務提示詞](PROMPT_CODEX_PSNR.md)：實作、驗證 PSNR、小型可重現報告，PR 僅改 PSNR 相關程式與輸出。
- [Work 任務提示詞](PROMPT_WORK_MATRIX_THEORY.md)：閱讀既有證據與書籍依據，撰寫教授可讀的數學推導及報告段落，PR 不碰 PSNR 程式或改動固定實驗設定。
- 兩者都先閱讀本文件及 [G6 報告](../reports/G6_SVD_QIM_QF15_SUCCESS.md)。每項任務獨立分支、PR、測試／自查，保留 CI 綠燈與原始負結果；請勿對相同檔案並行覆寫。
- 舊的 [reports/FINAL_REPORT.md](../reports/FINAL_REPORT.md) 是**早期不同題目（灰階圖低秩 JPEG）的歷史報告**，不可誤當 G6 浮水印專題正文；若要整合請新建 G6 專屬報告，避免破壞舊證據。

### 交付順序
1. Codex 提交真實 PSNR 數值與重現證據。
2. Work 完成獨立於 PSNR 數值的數學推導，可先寫佔位「PSNR 待測」，之後引用 Codex 證據整合。
3. 最終研究結論限於固定圖片、32-bit payload、實際測試的 QF 點；**不做 QF<15 機制研究、不聲稱全部整數 QF≥15 已測、不聲稱全域最佳參數。**
