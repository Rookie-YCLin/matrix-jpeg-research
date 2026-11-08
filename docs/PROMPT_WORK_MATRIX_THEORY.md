# Work 工作提示詞：G6 SVD-QIM 專題的完整矩陣理論推導（可直接複製至 ChatGPT Work）

請使用 Work mode 長篇深度工作、研究閱讀和必要的檔案編輯能力，針對 GitHub 倉庫 Rookie-YCLin/matrix-jpeg-research 產出一份教授可審查、具嚴格數學脈絡的繁體中文推導。若環境允許，請持續自行核對、修訂與提交 PR；不必等待使用者在兩小時內提供下一步指示。**不要虛構已經啟動的背景工作或宣稱存在長時間持續執行能力。**

## 資料來源與閱讀順序
1. docs/RESEARCH_NEXT_PHASE.md（最新主持人決策）
2. reports/G6_SVD_QIM_QF15_SUCCESS.md（已完成實驗；不重做）
3. patches/bwm_core_svd_d1_90.patch、experiments/svd_qim_validation.py、outputs/svd-qim-qf15-selected/results.csv 和 manifest。
4. guofei9987/blind_watermark 的固定 commit 322c90dc02d45644692095b34d3a6b735b6edbd8，確認 SVD 實際嵌入及擷取規則。
5. 主要數學參考：Dennis S. Bernstein, *Matrix Mathematics: Theory, Facts, and Formulas*, 2nd ed., Princeton University Press, 2009。已由主持人提供過 PDF；若本 Work 工作階段無法存取 PDF，請明確標註「尚待與原書核對」，不要假裝已親自讀取。重要位置：§5.6 pp.301–303（含 Theorem 5.6.4）、§9.2 pp.546–549（Frobenius）、§9.6 p.562（Proposition 9.6.8，可推出奇異值擾動界）。必要時補充公開、可查證來源，且分清引用與自行推導。

## 目標成品
在獨立工作分支新增 reports/SVD_QIM_MATRIX_THEORY.md，附一份教授口頭答辯可用的短版（可放在同檔末或 reports/SVD_QIM_DEFENSE_BRIEF.md）。若可操作 GitHub，開 PR 並在 CI/格式核查後自行完成授權範圍內的合併。**不要編輯 Codex 專責的 PSNR 程式／結果檔**。既有 reports/FINAL_REPORT.md 是歷史 JPEG 低秩研究，切勿當作此次浮水印 G6 的已完成報告或直接覆寫。

## 必要數學脈絡（逐步推導、定義符號、列假設）
A. 研究問題與控制變因：同一張血小板圖、固定 32 bits，原版 (36,20) vs G6 (90,20)；原始 SVD-QIM 為 guofei 開源實作，本研究只調 d1。
B. SVD：A=UΣV^T、奇異值排序、A'=UΣ'V^T。區分實際程式經 DWT/DCT 的區塊矩陣和最終 RGB 像素矩陣，避免把兩個空間混為一談。
C. 從 source code 推 QIM 格點：σ_i'=d_i(floor(σ_i/d_i)+1/4+b/2)；b=0 格點 k d_i+d_i/4、b=1 格點 k d_i+3d_i/4。實際解碼的 modulo/threshold 和兩通道 3:1 局部分數、跨區塊平均、最終 1D K-means，需以 pinned source 驗證；局部理想裕度 m=d/4，因此 9→22.5，提升 2.5 倍。
D. 擾動：定義在同一變換域同一區塊的 E；引入 |σ_i(A+E)−σ_i(A)|≤||E||₂，附從 Bernstein Proposition 9.6.8 出發的簡短正反向不等式推導；嚴格說明 ||E||₂<d_i/4 只是在理想格點及單一通道 QIM 判決下的充分條件，不保證實際 JPEG 或全域 K-means BER。別把 JPEG QF15 直接當成 E 的數值。
E. 失真：用正交不變性算 ||A'−A||_F²=(Δσ1)²+(Δσ2)²；考慮取整 QIM 推 |Δσ_i|≤3d_i/4，得到上界 (3/4)sqrt(d1²+d2²)；區分「可允許的最壞修改上界」與真實修改量。計算數學上兩個版本的上界並校對（(36,20)約30.88；(90,20)約69.14），不可寫成 PSNR 必然下降或實際增幅。
F. PSNR 從 RGB MSE=||I−J||_F²/(3HW) 到 10log10(255²/MSE) 的定義；如果 Codex 尚未量測，寫「待測」，不能補捏造數值。清楚區分嵌入後壓縮前 PSNR 與 QF15 壓縮後 PSNR，避免把 d1 的影響與 JPEG 攻擊造成的失真混淆。
G. 已有實驗：QF15 BER 32/32→0/32；QF15～95（每5）G6 BER0；明確限制單圖、固定 32bits、同一 JPEG encoder。QF5 已知 G6 32/32 錯，留於研究限制／附錄但**不要深究 QF<15 的機制**。原版 QF15 全 32 bits 反相現象尚未被證明原因，不可推定 K-means label swap。
H. 比較「數學定理／演算法定義／理論動機／實驗事實／尚未證明假說」並列出教授可能問的 5–8 個問題和有依據回答。不可宣稱 (90,20) 最優、全 QF≥15、跨多圖通用、我們發明 QIM。

## 交付品質
- 推導重視可讀性、每一步符號與假設，**不是堆一大堆定理**。
- 以 Bernstein 書中命題的準確名稱、書中印刷頁碼引用；書中若只列命題未給完整證明，就說明是本報告依命題作推導，勿誤稱原書附全證明。
- 引用 guofei upstream 授權與來源，不能整份上傳出版社 PDF 或大量複製書中文字。
- 不展開二維最佳化、QF<15 機理調查、更多影像／payload 長度測試。
- PR 說明包含論證主張與非主張、引用核對狀態、剩下的 PSNR 依賴、與 Codex 結果如何整合。

## 最後成果
完成正文可直接引用的論證稿、精簡答辯稿，以及 PR/commit/待整合項目連結；如無法直接更改 GitHub，請提供完整可複製 Markdown 與具體下一步，不要回報未真正執行的更動。
