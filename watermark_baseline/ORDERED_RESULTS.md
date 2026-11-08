# 零相位保序候選｜正式結果

本實驗疊接 [PR #21](https://github.com/Rookie-YCLin/matrix-jpeg-research/pull/21)。[執行前規格](ORDERED_PROTOCOL.md)與求解器在 `e7288807c917fe8a1b1aa59dd42b482c84c70a12` 固定。只有候選實例的區塊奇異值嵌入不同，兩組均由原圖重新嵌入、獨立 JPEG 編碼，使用相同的原版公開 bit 擷取。原版的 12 個重跑檔案與 W0/W0-D 封存的位元、PSNR、SHA-256 均一致。

## 正式比較

逐圖分母為 32，表格箭頭表示原版 → 保序。JPEG 均為 4:4:4。

| 影像 | 無攻擊 PNG | Q10 | Q20 | Q30 | PNG PSNR（dB） | Δ PNG PSNR（dB） | ≤0.5／≤1.0 dB |
|---|---:|---:|---:|---:|---:|---:|:---:|
| astronaut | 0 → 0 | 8 → 16 | 20 → 21 | 0 → 0 | 37.586 → 38.706 | +1.120 | 否／否 |
| chelsea | 0 → 0 | 0 → 2 | 26 → 25 | 0 → 0 | 38.088 → 39.430 | +1.341 | 否／否 |
| coffee | 0 → 0 | 4 → 6 | 32 → 32 | 0 → 0 | 38.198 → 39.505 | +1.307 | 否／否 |
| 合計錯誤／96 | 0 → 0 | 12 → 24 | 78 → 78 | 0 → 0 | — | — | 0/3／0/3 |

Q10 的 BER 從 12.50% 升到 25.00%，三張圖皆退步。Q20 仍為 81.25%，其中 astronaut 多錯一位、chelsea 少錯一位，coffee 仍 32 位全錯。兩組的無攻擊 PNG 與 Q30 均為零錯誤。

| 影像 | Q10 JPEG PSNR（dB） | Q20 JPEG PSNR（dB） | Q30 JPEG PSNR（dB） |
|---|---:|---:|---:|
| astronaut | 27.042 → 27.111 | 29.426 → 29.616 | 30.473 → 30.709 |
| chelsea | 28.317 → 28.411 | 30.362 → 30.782 | 31.489 → 31.913 |
| coffee | 26.220 → 26.233 | 28.039 → 28.230 | 29.157 → 29.289 |

兩種 PSNR 都以未嵌入原圖為參照。PNG PSNR 提高，表示本批影像上的嵌入失真較小。所有差值都超過事前指定的 ±0.5 dB 與 ±1.0 dB，因此兩種口徑均無相近品質配對。Q10 的退步是實測結果，無法據此分離較弱像素失真與保序約束對 BER 的作用。[逐位結果](../outputs/run-g5-ordered/results.csv) · [品質配對](../outputs/run-g5-ordered/paired.csv)

## 保序與邊界

在 29,754 個通道區塊，原版量化後前兩項換序 57 次，第二項落到第三項下方 2,027 次。保序候選的兩項計數均為 0。立即重分解後，原版第一／第二奇異值錯票為 32／374，候選皆為 0。寫成 PNG 後，原版錯票為 205／662，候選為 151／270。JPEG 後只可直接判讀降序的 SVD rank 及其票，這個排序不能證明原方向保留。每票共享影像及 payload，不能當作獨立樣本。[逐通道排序、票與區塊代價](../outputs/run-g5-ordered/ordering.csv)

合成測試以兩種 bit、零矩陣、重根、格點下界附近及隨機譜核對有限枚舉與窮舉全域解。測試覆蓋平手、Frobenius 代價、實際上游區塊讀回，並包含約束使區塊代價比原版增加和減少的例子。首次影像試跑中，觀測器在候選函式內抓不到 SVD 呼叫，因為候選匯入的是早先綁定的函式別名。改成從同一上游模組呼叫同一函式後，合成閘門重新通過，再從新目錄重跑。目標、格點、平手規則與品質門檻沒有改動。[首次執行紀錄](../outputs/g5-ordered-first-attempt.json) · [合成測試](../outputs/pytest-g5-synthetic.txt)

## 重跑與結論

```text
python -m pytest -v tests/test_ordered_embedding.py
python -m watermark_baseline.ordered_trial --output-dir outputs/run-g5-ordered-review
python -m watermark_baseline.ordered_trial --output-dir outputs/run-g5-ordered-review-repeat
python -m watermark_baseline.compare_runs outputs/run-g5-ordered-review outputs/run-g5-ordered-review-repeat
python -m pytest -v
```

兩個獨立目錄的 28 個索引檔案逐檔 SHA-256 相同。固定三張影像、一個 payload 與本編碼條件的結果顯示，這次確實修正量化換序，但未改善主要 Q10。候選搜尋到此結束。[manifest](../outputs/run-g5-ordered/manifest.json) · [重跑比對](../outputs/g5-ordered-replay.json) · [完整測試](../outputs/pytest-g5-ordered.txt)
