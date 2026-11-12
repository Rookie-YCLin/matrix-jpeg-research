# 論文導向 QF5–10 修正試驗：尚未修復

2026-11-12。三個有限候選皆未降低 QF5 BER，因此沒有替換 G6，也不宣稱完成抗低 QF 修正。固定原圖、32-bit payload、d2=20、keys=1、JPEG 4:4:4 與上游 SHA；未測 QF6–9，不能將兩端點結果外推至整段。

## 文獻與改編界線

Hwang, Lee, Lee, Kang, *SVD Based Adaptive QIM Watermarking on Stereo Audio Signals*, DOI [10.1109/TMM.2017.2721642](https://doi.org/10.1109/TMM.2017.2721642)。核對使用者提供的 accepted manuscript 第4頁 Eq.(14)–(16)、第5頁 Eq.(24) 及第8頁 Appendix B。PDF SHA256：`32544f9d3821107524b58a306841a3b2b0dda9862673a42c104e965446899818`。不在倉庫再散布全文。

論文將兩聲道構成 rank-2 矩陣，嵌入 σ1'=σ2 Q(σ1/σ2;b,Δ)，解碼使用收到的奇異值比值。共同增益 a>0 時，σi(aA)=aσi(A)，因此比值不變。這不等於任意 JPEG 擾動的比值不變。本專題的 4×4 洗牌 DCT 矩陣不是論文的雙聲道矩陣，不能挪用 mid/side 能量解釋或 MP3 實驗作 JPEG 結論。

Eq.(24) 是 Δ[floor(x/Δ+1/2)+(2b−1)/4]；它與上游 floor(x/d)+1/4+b/2 不同。本輪中心化候選使用該式，保留第二奇異值原有 QIM。比值候選使用 t=max(σ2',90)，Δ=1，故有效步長 t≥90，不能稱為固定 d1=90；這個截斷也破壞一般尺度不變性。第三候選是在失敗診斷後事先登記的最近合法格點 90(k+b/2)，屬本研究改編，不是論文原式。

## 配對實測

每格為錯誤數／32 bits。新候選均為實際重新嵌入、PNG 保存、JPEG 編解碼及盲式擷取，沒有按 QF 翻轉位元。

| 方法 | PNG | QF5 | QF10 | QF15 | QF20 |
|---|---:|---:|---:|---:|---:|
| 原版 (36,20) | 0 | 12 | 1 | 32 | 32 |
| G6 (90,20) | 0 | 32 | 0 | 0 | 0 |
| paper_centered90 | 0 | 32 | 0 | 0 | 0 |
| paper_ratio_floor90 | 0 | 32 | 0 | 0 | 0 |
| paper_nearest_zero90 | 0 | 32 | 0 | 0 | 0 |

QF5 新候選相對 G6 BER 降幅均為0%，不符合預登記至少5%改善；它們也都比原版12/32差。QF10 沒有重現「驟升」，G6及三候選皆0%。所有負結果都保存，沒有選優後隱藏結果。PSNR/MSE 同時寫入 CSV 供檢查嵌入代價，但不據此宣稱 BER 改善。

## 診斷與可證明的限制

G6 的 QF5 圖片在 Y/U/V 三通道、真實 bit=0/1 各組，第二奇異值中位數全部為0。這只代表各組中位數，不代表每一塊全為0。第一奇異值相對已保存 PNG 的有號擾動範圍超過 ±22.5；22.5 是90/4的局部理想裕度，不是 JPEG 噪聲上界。

QF5 第一奇異值硬判為1的比例如下（離線使用真值分組；不供解碼）：

| 通道 | 真實bit0 | 真實bit1 |
|---|---:|---:|
| Y | 37.624% | 21.925% |
| U | 38.869% | 22.255% |
| V | 2.174% | 15.231% |

Y/U 的群組次序在進入 K-means 前已反轉，V則不同；因此不能把全部錯誤簡化成 K-means 任意交換標籤。本表僅診斷第一奇異值，尚非整個3:1雙奇異值融合及跨塊平均的完整因果證明，也不允許依真值挑選通道當「盲式」修復。

令水印矩陣奇異值為 s1≥s2>0，收到值為 s1+e1、s2+e2。若 |ei|≤ε<s2，則

`|(s1+e1)/(s2+e2) − s1/s2| ≤ ε(s1+s2) / [s2(s2−ε)]`。

這由通分後分子 |s2 e1−s1 e2|≤ε(s1+s2)、分母 ≥s2(s2−ε) 得到。分母小或 ε≥s2 時不能使用此保證。JPEG 使大量第二奇異值消失，故直接比值化缺少穩定性依據。論文 Appendix B 也討論加性噪聲的弱點，並未保證所有壓縮都有效。

## 證據與重跑

- [事前方案與追加記錄](../docs/PAPER_LOW_QF_PLAN.md)
- [第一輪完整 CSV](../outputs/paper-low-qf-initial/results.csv)、[manifest](../outputs/paper-low-qf-initial/manifest.json)，同目錄保留來源／標記／攻擊影像與符合 manifest code hash 的原始程式快照。
- [第三候選 CSV](../outputs/paper-low-qf-nearest/results.csv)、[manifest](../outputs/paper-low-qf-nearest/manifest.json)
- [診斷原始結果](../outputs/paper-low-qf-diagnostic.json)、[可重跑版及輸入雜湊](../outputs/paper-low-qf-diagnostic-replay.json)
- [實作](../experiments/paper_low_qf.py)、[診斷腳本](../experiments/paper_low_qf_diagnostic.py)

使用既有固定 upstream 環境，設定 OPENBLAS_NUM_THREADS=1：

```text
python -m experiments.paper_low_qf --output-dir outputs/paper-local
python -m experiments.paper_low_qf --output-dir outputs/paper-nearest-local --variants paper_nearest_zero90
python -m experiments.paper_low_qf_diagnostic --input-dir outputs/paper-local --output outputs/paper-diagnostic-local.json
python -m pytest -q
```

本機完整測試29通過，含8項新QIM格點／裕度／盲式介面檢查。兩次診斷除新增 provenance 外數值一致。第一輪程式快照與最終程式對既有兩候選使用相同公式；第三候選 manifest 對應最終實驗程式 SHA256。

本輪依事前上限停止候選，未跑成功候選才需要的19點驗證。後續有效研究需要另立能應對非共同縮放與小分母的假說；不能只引用論文、增加步長或翻轉真值來聲稱已修復。
