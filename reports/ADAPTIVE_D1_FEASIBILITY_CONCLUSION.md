# 自適應量化步長可行性：目前證據的結論

本報告整合架構盤點、固定主圖的完整 Grid、等預算搜尋器比較，以及現有影像資料清點。所有「已驗證」數字限於固定上游版本、32-bit payload、`d2=20`、Pillow RGB 4:4:4 JPEG 與 QF5–10。

## 已驗證的結果

1. `d1` 可在不改寫核心的情況下，於嵌入與盲式擷取端同步設定；`d2=20`、DWT/DCT/SVD、3:1 融合與 K-means 均可固定。
2. 對指定主圖完整枚舉 `d1=1…150` 共 900 個 JPEG BER 測量後，BER 對 `d1` 是非單調且有跳躍的。各 QF 的最小零錯步長不同（QF5=14、6=27、7=34、8=20、9=29、10=25）。
3. 模型 A（QF5–10 均 0/32、PNG PSNR≥40 dB）在該域 **不可行**。最小全零 BER 是 `d1=140`，PNG PSNR 28.240 dB；PSNR≥40 dB 的最佳平均 BER 則仍是 0.20833。
4. 模型 B 的固定 `λ=0.5` 折衷最佳值為 `d1=33`：平均 BER 0.05729、最壞 BER 0.3125、PNG PSNR 38.755 dB。它不是 Model A 的可行解，不能誤稱為零 BER。
5. 在單圖、24 次有效評估、10 固定 seeds 下，BO 的 Grid-oracle 命中數是 5/10、DE 3/10、PSO 與 Random 皆為 0/10；此為 BO／DE 在這一個離散 objective 上較有希望的**初步支持**。

## 八個研究問題

| 問題 | 目前回答 | 判定 |
|---|---|---|
| PSO 能否找到同時滿足 BER 與 PSNR 的 `d1`？ | 本次 PSO 沒有命中 Model B oracle；而 Grid 已證明 Model A 在 1–150 無可行解，故不存在可由 PSO 找到的 Model-A 解。 | 已驗證（此域） |
| DE、BO 是否比 PSO 更適合？ | 在相同 24 次預算的單圖結果，BO/DE 平均 objective 較小且有 oracle hits。 | 初步支持 |
| PSO 是否比 Grid 節省計算成本？ | PSO 用 24 次而 Grid 用 150 次，但未命中 oracle；Grid 在這個小域才提供完整可行性與 Pareto 真值。 | 已驗證：不能宣稱 PSO 較合適 |
| 不同影像的最佳 `d1` 是否有差異？ | 尚無跨影像的 Grid labels。 | 尚未驗證 |
| 可否由 DWT/DCT/SVD 特徵預測最佳 `d1`？ | 特徵可不嵌入水印地萃取；但沒有足夠的圖像—最佳步長配對資料可訓練或測試。 | 尚未驗證 |
| 可否不反覆 JPEG BER 測試而選 `d1`？ | 尚無經獨立測試的預測模型。 | 尚未驗證 |
| QF5–10 零 BER 為何失敗？ | Grid 直接證明目前 40 dB 限制與全零可靠性衝突；提高 `d1` 至 140 可達全零但造成明顯失真。JPEG、QIM 的離散判決與後續融合皆可能參與，現有證據不能歸因於單一因素。 | 已驗證取捨；歸因尚未驗證 |
| 最值得發展的正式方法？ | 現階段建議以 Grid 建標籤、BO/DE 作低預算離線搜尋對照，之後才比較可解釋的特徵規則；不建議在 11 張圖上使用深度學習。 | 初步支持 |

## 特徵與資料限制

新建的 `experiments.adaptive_d1_features` 可從原圖萃取灰階均值／變異數、Sobel 梯度、Haar DWT 頻帶能量、低/高頻 DCT 能量、與 4×4 DCT-SVD 頻譜統計，完全不嵌入水印或使用 BER。已對使用者允許的本機 Test 目錄完成 10 張圖的特徵清點；其輸出明確標記 `features_only_no_d1_labels`。

但版本庫只有 `data/ascent.png`，加上本機 10 張圖仍僅 11 張獨立影像，距離 30/10/10 split 所需 50 張少至少 39 張。不得以重複壓縮、裁切或增強版本跨 split 充數。下一步應取得有來源／授權／SHA-256 manifest 的公開影像資料集（例如固定的 Kodak、DIV2K 或 COCO 子集），建立 50 張不重疊清單後才執行每圖離線 Grid、訓練、驗證與真正的未見測試。

因此，本回合沒有報告虛構的跨影像預測 BER、SSIM、泛化率或 train/validation/test 成績。要完成正式自適應模型，必須先補齊上述資料並把 SSIM 納入每張實測標記影像的品質量測。

相關證據：[架構](ADAPTIVE_D1_PHASE1_ARCHITECTURE.md)、[Grid](ADAPTIVE_D1_GRID_QF5_QF10.md)、[搜尋器](ADAPTIVE_D1_OPTIMIZER_BENCHMARK.md)。
