# 自適應 `d1`：Grid 真值基線（QF5–10）

日期：2026-11-13  
狀態：**已驗證（固定主圖的完整整數 Grid）；不是跨影像泛化結論。**

## 設定

這次實驗只改執行期的第一奇異值 QIM 步長 `d1`，完整枚舉 `1,…,150`；`d2=20`、32-bit payload、兩把 key、完整 SVD、DWT/DCT、原版 3:1 融合、K-means 與盲式擷取規則都不變。每個 `d1` 重新嵌入一次，先量測 RGB PNG PSNR，再以 Pillow RGB 4:4:4（`subsampling=0`、`optimize=False`、`progressive=False`）壓縮並盲式擷取 QF=5、6、7、8、9、10。

總共產生 900 個 JPEG BER 量測（150 個 `d1` × 6 個 QF），實測核心計算時間為 1559.364 秒。設定、固定來源雜湊、套件／JPEG 版本、檔案雜湊、逐點資料與 SVG 均封存於 [`outputs/adaptive-d1-grid-qf5-qf10-d1-1-150`](../outputs/adaptive-d1-grid-qf5-qf10-d1-1-150)。

## 模型 A：最小滿足零 BER 與 40 dB 的 `d1`

模型 A 要求 QF5–10 每一點都是 0/32，且 PNG PSNR 至少 40 dB。結果：**infeasible**，但限定在這張圖、固定 payload／codec、整數 `d1=1…150` 和 40 dB 門檻。

- 每個 QF 單獨都存在零錯誤步長：最小零錯 `d1` 分別是 QF5=14、QF6=27、QF7=34、QF8=20、QF9=29、QF10=25；這是 BER 對 `d1` 非單調的直接證據。
- 全部六個 QF 同時 0/32 的最小值是 `d1=140`，但其 PNG PSNR 僅 **28.240 dB**，遠低於 40 dB。`d1=140…150` 都有全零 BER，PSNR 範圍 27.447–28.358 dB。
- PNG PSNR 至少 40 dB 的候選共有 26 個；其中平均 BER 最低的是 `d1=16`，平均 BER **0.20833**、最壞 BER **0.375**、PSNR **41.460 dB**，仍不是零 BER。

所以本結果不表示「不存在更大 `d1` 或其他演算法的解」，只表示已預先固定的域與條件中沒有同時達標的整數解。

## 模型 B：固定權重的 BER–失真折衷

使用

\[
J_{0.5}=0.5\,\overline{\mathrm{BER}}+0.5\max\{0,(40-\mathrm{PSNR})/40\}.
\]

完整 Grid 的唯一依同分最小 `d1` 規則選出的模型 B 最佳點為：

| `d1` | 平均 BER（QF5–10） | 最壞 BER | PNG PSNR | `J₀.₅` |
|---:|---:|---:|---:|---:|
| 33 | 0.0572917 | 0.3125 | 38.755 dB | 0.0442100 |

作為對照，純 BER 最佳值由 `d1=140` 起達成全零，但 PNG PSNR 為 28.240 dB、`J₀.₅=0.147004`。這個差異說明 Model B 並非「找 BER 最低的 `d1`」；它是預先定義的品質—可靠性折衷。最壞 BER必須持續獨立報告，不能只看平均值。

## 可重現性與限制

- `per_qf.csv` 有 900 列且每一個 QF 都恰有 150 列；`per_d1.csv` 有 150 列。所有候選的未攻擊 PNG 都正確解出 32 bits。
- BER 的分母固定為 32；例如最壞 BER 0.3125 就是 10/32，而非估計的連續機率。
- 結果僅針對指定主圖。它不能替代未見影像的訓練／驗證／測試，亦不能宣稱最佳步長具有普遍性。
- Grid 是這個有限域內的 oracle。接下來 Random、PSO、DE 和 BO 必須以相同有效評估預算、固定多個 seeds、相同快取規則比較其逼近此 oracle 的速度與穩定性；它們不會重新定義或覆蓋 Grid 結論。

## 產物

- [設定](../outputs/adaptive-d1-grid-qf5-qf10-d1-1-150/config.json)
- [逐 QF 結果](../outputs/adaptive-d1-grid-qf5-qf10-d1-1-150/per_qf.csv)
- [逐 `d1` 摘要](../outputs/adaptive-d1-grid-qf5-qf10-d1-1-150/per_d1.csv)
- [BER–`d1` 圖](../outputs/adaptive-d1-grid-qf5-qf10-d1-1-150/ber_vs_d1.svg) · [PSNR–`d1` 圖](../outputs/adaptive-d1-grid-qf5-qf10-d1-1-150/psnr_vs_d1.svg) · [Pareto 圖](../outputs/adaptive-d1-grid-qf5-qf10-d1-1-150/pareto_psnr_worst_ber.svg)
- [執行 manifest](../outputs/adaptive-d1-grid-qf5-qf10-d1-1-150/manifest.json)
