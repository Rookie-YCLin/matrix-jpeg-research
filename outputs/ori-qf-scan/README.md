# W1 原版 BER–QF 實測｜唯一測試影像 ori_img.jpeg

## 結果（2026-11-08，GitHub Actions）

- [實驗 run #42461739759](https://github.com/Rookie-YCLin/matrix-jpeg-research/actions/runs/42461739759)：兩個 CI 工作成功；[PR #24](https://github.com/Rookie-YCLin/matrix-jpeg-research/pull/24)。
- **來源**：使用者選定的 [上游 ori_img.jpeg](https://github.com/guofei9987/blind_watermark/blob/master/examples/pic/ori_img.jpeg)，實際取得 RGB 1108×738×3；Git blob SHA `ef48a056b3cab1d2c08723c014d8d515963f5a07`；SHA-256 `17bed8cfeb5534351d2f35d4addd9407e0c0132132444276a0f826c7ae9923c2`。
- **演算法**：上游固定提交 `322c90dc02d45644692095b34d3a6b735b6edbd8`、common、非 fast SVD 4×4、兩個量化步長 36／20；payload `10110010111001000101101011010001`（32 bit），固定金鑰與原版公開 bit API。
- **攻擊**：由原版標記後的 PNG 各自編碼 JPEG，Pillow RGB、4:4:4、optimize=False、progressive=False，QF=5、10、…、95，共 19 條件。
- **無攻擊 PNG**：0／32 錯誤。
- **最大 BER**：QF=15 和 20 都為 32／32（100%），依事先固定的「並列選最小 QF」規則，**正式 x=15**。
- 其他重要值：QF=5 為 12／32（37.5%）；QF=10 為 1／32（3.125%）；QF=25–95 均為 0／32。
- **異常診斷線索**：在 QF=15 與 20，32 個擷取位元逐位恰好是原始 payload 的互補值。此結果支持「全域位元極性反轉」的觀察，但不能僅由 BER 判定反轉的真正原因，也不能將知道原始 payload 後的反相修復冒充盲式 SVD 抗 JPEG 改善。
- **下一階段**：先以完整盲式管線診斷 K-means 兩群方向、SVD 餘數投票分布等，再設計 SVD 區塊候選，固定在 QF=15 與此 32-bit payload 比較；不更換 x。正式性能只報 BER，無 PSNR。

## 既定相對改善門檻及整數位元解析度

原版 QF=15 的 BER=32／32=1；對候選若仍解出 32 位元，定義相對 BER 降幅：

`R=(32 - candidate_error_count)/32 × 100%`。

- **達標 R≥5%**：候選至多 **30／32** 錯誤（改善至少 2 位，R≥6.25%）。
- **優秀 R≥10%**：候選至多 **28／32** 錯誤（改善至少 4 位，R≥12.5%）。
- 因單圖單一 payload 只有 32 位元，單一位元變化即 3.125 個百分點；不能因此宣稱在其他影像／payload 也具有相同效果。

## 保存與重現

- [results.csv](results.csv)：19 個 QF 的逐位輸出與 BER，由 workflow 實際 stdout 原樣取回；[manifest.json](manifest.json)：該次運行的來源、環境與檔案雜湊。
- [GitHub Actions artifacts](https://github.com/Rookie-YCLin/matrix-jpeg-research/actions/runs/42461739759)：完整 marked.png、19 個受攻擊 JPEG、原始 ori_img.jpeg、CSV 與 manifest；artifact 具有保留期限，長期追溯以 Git 的 CSV／manifest 為主。
- 重跑：在具備 Python 3.13、固定上游安裝及對應影像下載環境下執行 `python -m experiments.ori_qf_scan --output-dir outputs/ori-qf-run-new`；輸出目錄必須不存在。

> 本次是第一步**原版基準**，沒有測試 SVD 改良候選，也尚未達成降低 BER 的最終目標。
