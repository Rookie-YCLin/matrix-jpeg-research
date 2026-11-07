# 一週研究章程｜秩一 SVD 與 JPEG 區塊 DCT

研究者於 2026-11-08 正式批准《基於 SVD 秩一分解與區塊 DCT 頻譜之 JPEG 壓縮穩定性分析》。[Issue #11](https://github.com/Rookie-YCLin/matrix-jpeg-research/issues/11) 是 Codex 唯一有效的新實驗工作包。[Issue #8](https://github.com/Rookie-YCLin/matrix-jpeg-research/issues/8) 保存正式決策，[Issue #10](https://github.com/Rookie-YCLin/matrix-jpeg-research/issues/10) 的舊 W0/G1 浮水印工作包已暫緩。禁止執行舊浮水印工作、嵌入／擷取開發及 BER 實驗。R2 暫緩。

一週內交付題目明確、有矩陣理論深度、數據可重現的課程報告。先建立並審查 R1 的數學與重現證據，再依研究者指示決定是否啟動 R2。浮水印只作動機或未來應用。

## R1 已授權的範圍

固定 512×512 灰階 `data/ascent.png` 與既有 Q40、Q60、Q80、Q95 JPEG。用 float64 取原圖 SVD。對每個原圖秩一方向的左右向量各做分塊正交 8 點 DCT。由可分離性，區塊二維係數是兩個一維係數的乘積。兩個邊際頻率能量的外積 Wᵢ 非負、大小 8×8，由 Parseval 與單位範數可知總和為 1。實作須逐方向驗證這些性質，並依實際 JPEG 量化表計算 Sᵢ(Q) = sqrt(Σₖₗ Wᵢ[k,l] Δ_Q[k,l]²)。量化表排列必須驗證，完整範圍及驗收以 Issue #11 為準。

## 待驗證的關係與研究限制

Sᵢ(Q) 與實際誤差是否相關是研究問題。R2 若另獲授權，才計算 eᵢ(Q) = |uᵢᵀ(B_Q − A)vᵢ|，並控制 σᵢ 做描述性 partial Spearman 與圖表。eᵢ(Q) 衡量原圖方向的投影誤差，與重算 JPEG 的奇異值變化是不同量。單張影像及四種品質的結果不作跨影像統計顯著性、抗壓能力提升或 BER 改善主張。

## 審查與歷史

保留 `main` 的 `PROJECT_SPEC.md`、`experiment.py`、既有 13 項測試、`outputs/run-m2/` 及歷史 CSV。[PR #7](https://github.com/Rookie-YCLin/matrix-jpeg-research/pull/7) 保持開啟、未合併，分支與內容完整保留。禁止直接修改 `main` 或自動合併 PR。

由研究者決定是否接受成果及進入下一階段。R1 PR 附 CSV、manifest、確切命令、測試與限制。圖表由實際 CSV 產生。舊版 G0=A 與 W0/G1 章程保存在 [PR #9 的前版提交](https://github.com/Rookie-YCLin/matrix-jpeg-research/tree/070110609d11f6b7ed25d820e87bf7a020bc02fb)，僅供追溯。
