# G6：將第一奇異值 QIM 步長由 36 改為 90（QF15 已達標）

## 研究問題與預先固定的規則

- 上游：[guofei9987/blind_watermark](https://github.com/guofei9987/blind_watermark)，提交 `322c90dc02d45644692095b34d3a6b735b6edbd8`；唯一影像是指定 `examples/pic/ori_img.jpeg`，來源 Git blob `ef48a056b3cab1d2c08723c014d8d515963f5a07`。
- 正式主 JPEG QF：由**原版** QF=5～95 每5的全掃描事前選出，QF15、QF20 都是 32/32 錯；並列取最小值，因此 **x=15**。選 x 在 G6 候選測試之前完成。
- 標準：相對 BER 降幅 `R = (BER_original(15)-BER_modified(15))/BER_original(15) × 100%`，R≥5% 達標，R≥10% 優秀。

## 實際 SVD 改良

- 只修改上游 `WaterMarkCore.__init__` 中供 SVD 區塊 QIM 嵌入／擷取使用的 **第一奇異值量化步長**：`self.d1, self.d2 = 36, 20` → **`90, 20`**。第二奇異值步長不變；DWT、DCT、排列／金鑰、三色通道、3:1 融合、跨區塊平均與原版 1D K-means 均不變。
- 原版嵌入 `s0 <- d1 ( floor(s0/d1) + 1/4 + b/2 )`，解碼 `b0 = 1[(s0 mod d1)>d1/2]`。只把 d1 換成 90，並在嵌入與盲式擷取使用同一步長；**沒有使用真實 payload 當作解碼端資訊**。
- 對應的最小修改可參考 [SVD 原始碼 patch](../patches/bwm_core_svd_d1_90.patch)；CI 透過 Python 實例中設定 `bwm_core.d1=90` 進行等價驗證，並未直接改動上游發行套件。

## 已驗證 BER 結果

| JPEG QF | 原版錯誤 /32 | G6 錯誤 /32 | 說明 |
|---:|---:|---:|---|
| 5 | 12 | 32 | **重要限制：G6 在更強壓縮 QF5 反而變差** |
| 10 | 1 | 0 | 改善 |
| **15（正式主條件）** | **32** | **0** | **相對 BER 降幅 100%，達優秀門檻** |
| 20 | 32 | 0 | 改善 |
| 25–95（每5） | 0 | 0 | 維持 0 錯誤 |

- 原版與 G6 的無攻擊 PNG 在所有三個位元序列均為 **0/32 錯誤**。
- **事後新增、未用於候選搜尋的兩組位元**（相同唯一測試圖及金鑰）：16個1的不同 32-bit payload、與原版 payload 的逐位互補，在 QF15 原版皆 32/32 錯，G6 皆 0/32；QF10、20、25 也測到 G6 0/32。
- 先跑15組預先列表的 QIM 步長候選；並非每一組有效，保留 [全候選表](../outputs/svd-qim-qf15-exploration/results.csv) 作內部研究證據。G6 選擇 `d1=90,d2=20` 是因為**只變一個參數**，且先前探索於 QF10、15、20、25 均為 0/32；正式二次驗證覆蓋完整 QF 曲線與兩組未參與設計的 payload。

## 矩陣理論與適用限制

上游 QIM 設定 0、1 的奇異值格點殘餘分別為 `d1/4`、`3d1/4`，離二元判決界線的理想距離為 `d1/4`。把第一奇異值步長由 36 改為 90，使該理想裕度由 **9** 增至 **22.5**（2.5 倍）。若嵌入矩陣的第一奇異值確實位於欲指定的格點、無排序影響，且受攻擊後的同一區塊矩陣擾動為 E，則奇異值擾動界

`|σ₀(A+E)-σ₀(A)| ≤ ||E||₂`

意味著當 `||E||₂ < 22.5` 時第一奇異值的 QIM 位元不會跨界。**這僅是理想局部充分條件，並不證明 JPEG 攻擊一定滿足它，更不能直接推導本系統最終 BER**；最終 BER 是實測結果。

**結論的限定**：本報告的成功僅針對事前指定的 QF15、單張測試圖及固定 JPEG 編碼器／金鑰；對 QF5 並沒有改善，故不可宣稱 G6 在所有低 QF 都更強韌。依使用者本專題的 QF=x 驗收規則，此方案已達標且屬優秀；未量測也不要求 PSNR。

## 可重現證據

- [第一次探索 CI](https://github.com/Rookie-YCLin/matrix-jpeg-research/actions/runs/42463006848)：15組候選、四個 QF，含完整實驗原檔。
- [完整驗證 CI](https://github.com/Rookie-YCLin/matrix-jpeg-research/actions/runs/42463429539)：原版和 G6 完整19點 QF、兩個新增位元序列、PNG 全部通過。CI 中 `svd-qim-selected-validation` job 成功。
- [探索 CSV](../outputs/svd-qim-qf15-exploration/results.csv) · [探索 manifest](../outputs/svd-qim-qf15-exploration/manifest.json) · [驗證 CSV](../outputs/svd-qim-qf15-selected/results.csv) · [驗證 manifest](../outputs/svd-qim-qf15-selected/manifest.json)。
- 重跑：按照 `.github/workflows/research-ci.yml` 固定安裝 PyWavelets、OpenCV 及 pinned upstream，再執行 `python -m experiments.svd_qim_validation --output-dir <new-empty-dir>`。不重複選 x，不用正確 payload 幫助解碼。

