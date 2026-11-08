# Codex 工作提示詞：僅完成 G6 的 PSNR 對照（可直接複製至 Codex）

你是研究倉庫 Rookie-YCLin/matrix-jpeg-research 的實作工程師。請自主、仔細完成這項可重現 PSNR 交付；使用你可用的工作時段深入測試、排除資料／單位／編碼錯誤，**不需等待使用者回來**，但不可承諾外部環境允許的執行時長。使用獨立分支與 PR；若 CI 通過且經自審可以直接合併 main（倉庫已有主持人授權）。

## 先讀
1. docs/RESEARCH_NEXT_PHASE.md（最高優先最新規格）
2. reports/G6_SVD_QIM_QF15_SUCCESS.md
3. experiments/svd_qim_validation.py、experiments/ori_qf_scan.py、experiments/svd_qim_sweep.py
4. outputs/svd-qim-qf15-selected/results.csv、manifest.json
5. .github/workflows/research-ci.yml、AGENTS.md（較舊衝突內容以最新 handoff 為準）

## 任務（只做 PSNR，絕對不要重新搜尋 d1,d2）
- 固定唯一原始血小板圖 examples/pic/ori_img.jpeg（核對 Git blob、SHA256）；固定原 payload 10110010111001000101101011010001、password_img=password_wm=1、full SVD、upstream pin 322c90dc02d45644692095b34d3a6b735b6edbd8。
- 僅比較 baseline (36,20) 與 G6 (90,20)；公平使用相同 JPEG QF15 4:4:4 subsampling=0, optimize=False, progressive=False。
- 對每組嵌入一次到 PNG、再從各自 PNG 產生 QF15 JPEG。用解碼後 RGB 整數影像計算：(a) 原圖 vs 無損嵌入 PNG 的 PSNR；(b) 原圖 vs QF15 壓縮圖的 PSNR（主要）。兩者都提供 MSE、PSNR dB、PSNR_G6−PSNR_upstream dB。
- 逐通道 RGB 使用 float64 計算，嚴防 uint8 subtraction overflow、shape mismatch、混用 cv2 BGR/Pillow RGB、圖片不同尺寸、JPEG encoder drift。MSE=0 時 PSNR=+inf；所有表頭清楚標「uncompressed embedded」與「QF15 attacked」。
- 新增最小且可重用的 PSNR module 或 CLI（例如 experiments/svd_qim_psnr.py）、單元測試與清楚可重跑的命令；僅新增必要的資料輸出（CSV/JSON manifest）及 reports/SVD_QIM_PSNR_TRADEOFF.md。記錄原始 SHA256、產物 hash、版本、保存所有有限對照結果。
- 若成本合適，交叉核對已存 BER（QF15 baseline 32/32、G6 0/32）但**不可重跑 15 候選搜尋**、不可重測 QF<15 的失效機制，亦不需掃描 QF16–94；如無必要，不重跑完整 BER CI。
- 說明「影像品質代價」必須由實際 PSNR 結果決定；如果 G6 PSNR 比 baseline 更高，要如實說明，不可為迎合 trade-off 而偽造下降。主要 QF15 PSNR 混合嵌入和 JPEG 誤差，次要無攻擊 PSNR 才更接近嵌入代價。
- 不引入第二張圖、不更換 32-bit payload、不優化 d2、不調選參數、不修改 upstream 核心算法、不改舊實驗數值／圖檔／hash。
- 完成後 PR body 必須有實測數字／來源檔、重現步驟、執行耗時或測試數、限制、CI 狀態及檔案連結。若不能執行（環境/依賴/授權），明列阻礙，不要把待測標成已測。

## 驗收
一份可信且可以重現的配對表、PSNR 計算可單元測試、最小 CI 檢查或明確本地驗證、研究結論不誇大。所有資料須由實際運算產生，不能使用示意數據充當實測。
