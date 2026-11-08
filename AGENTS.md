# 研究代理規格｜唯一圖、最大 BER QF、SVD 改良

## 已指定的唯一測試圖與最大 BER 選點規則（最新）

- 單一來源：[上游指定測試圖](https://github.com/guofei9987/blind_watermark/blob/master/examples/pic/ori_img.jpeg)；固定上游 blob SHA `ef48a056b3cab1d2c08723c014d8d515963f5a07`，下載後另核 SHA-256。
- 原版先跑 **QF 5 的倍數**的 BER 掃描，預設建議 5–95 每 5 一點，待主持人核定；`x` 為原版最高 BER 的 QF。並列最高時先定 tie-break。不能挑候選較好的點替換 `x`。
- 改良 SVD 在凍結的同一 `x` 比較 BER，目標進步 ≥5%，10% 優秀。**5% 是相對降幅或百分點，未定，必須向主持人請示**；報錯誤數和實際分母。
- 以前三張圖 QF10 的 12/96 只屬歷史探索；不能作唯一新圖的基準。新的 QF 掃描尚未執行。
- 正式性能指標只須 BER，不加 PSNR；其餘維持三步驟、可重現與逐輪 Draft PR 審查要求。


**最高研究目的**：根據 [guofei9987/blind_watermark](https://github.com/guofei9987/blind_watermark) 的 [bwm_core.py](https://github.com/guofei9987/blind_watermark/blob/master/blind_watermark/bwm_core.py)，自行改良 SVD 區塊的**嵌入或擷取**，降低低 JPEG QF 的浮水印 BER。

1. **先重現原版**：上游 [att.py](https://github.com/guofei9987/blind_watermark/blob/master/blind_watermark/att.py) 未含本專題所需 JPEG 壓縮測試；另建 JPEG 攻擊、QF 掃描、原版 bit 擷取與 BER 評估。實驗固定上游 SHA，逐圖逐 QF 保留 CSV／manifest／來源／環境／seed。
2. **只用 BER 衡量正式性能**：不要求 PSNR；不能把排序、Frobenius 範數或數學證明當作抗 JPEG 成果。新增方法須保留可解釋的矩陣理論依據。
3. **反覆迭代到正向結果**：本規格**取代過去「G5 後禁止所有候選」的指示**。在既有研究範圍內可構思新 SVD 候選，但每輪正式實作／重測／重大變更前向主持人報告設計並取得同意；不做無限參數搜尋或事後更換成功門檻。找到預先界定且可重現的 BER 改善即停止候選搜尋。
4. **正式報告聚焦成功方法**：不強迫逐一描述失敗試驗；但內部必須保留全部已做實驗（含負結果），不得偽造、篡改或用選擇性呈現造成不實結論。
5. **專案管理**：每次使用 [專題倉庫](https://github.com/Rookie-YCLin/matrix-jpeg-research)，核對 [正式規格](PROJECT_SPEC.md)、[實驗索引](docs/EXPERIMENT_INDEX.md)、[交接](docs/CODEX_NEXT_SESSION.md) 與 [PROGRESS](PROGRESS.md)。獨立分支＋Draft PR，不直接修改 main；依需要新增、修訂、移除*經確認無依賴的冗餘*內容，不能自行刪除實驗原始資料、上游授權或歷史 PR。任何合併須主持人明確批准。
6. **主動回報與請示**：每輪回報目前階段、完成事項、各 QF BER、阻礙、下一步及待決事項。遇到比較標準、設計方向、非 SVD 模組、破壞性刪檔等不確定事項要向主持人提問，而不是自行決定；不宣稱可以無人觸發地背景執行。
