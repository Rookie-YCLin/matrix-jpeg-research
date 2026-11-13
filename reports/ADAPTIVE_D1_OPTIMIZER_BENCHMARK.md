# Model B 的預算匹配搜尋器比較

狀態：**初步支持；單一影像、以完整 Grid 的實測值作 oracle。**

四個搜尋器都在相同離散域 `d1=1…150`、相同 Model B `J₀.₅`、每 seed 24 個不重複有效評估、seeds 0–9 下比較。每一次「評估」均查閱先前完整 JPEG QF5–10 Grid 的真實 BER／PSNR；因此此比較不會把 surrogate 預測或重複查點算作新的影像實驗。

| 方法 | seeds | 每 seed 有效評估 | 平均最終 `J₀.₅` | 最佳最終 `J₀.₅` | 命中 Grid oracle |
|---|---:|---:|---:|---:|---:|
| Random | 10 | 24 | 0.0983193 | 0.0451369 | 0/10 |
| PSO | 10 | 24 | 0.0855722 | 0.0451369 | 0/10 |
| DE | 10 | 24 | 0.0729312 | 0.0442100 | 3/10 |
| BO | 10 | 24 | **0.0620455** | **0.0442100** | **5/10** |

完整 Grid oracle 是 `d1=33`、`J₀.₅=0.0442100`。在這個有限實驗中，BO 的平均 best-so-far 值與命中數最好，DE 次之；這是**初步支持** BO／DE 在此非單調離散曲線上較有效率，並非對其他圖片、PSNR 門檻、預算或超參數的通用宣稱。演算法本身的純計算時間很小；真正部署時的成本由一次完整 JPEG BER 評估主導（Grid 實測約 10 秒量級／候選），故以有效評估數作公平基準。

PSO 與 DE 的連續位置在每次提案時 clip 並 round 到 `[1,150]`；若落在已評估整數，改取尚未評估的隨機整數，且不重複計數。BO 使用 RBF Gaussian-process surrogate、六個隨機初始點與 expected improvement；所有 seed、預算與方法清單已在 config 固定。

產物：[設定](../outputs/adaptive-d1-optimizer-benchmark/config.json)、[逐次軌跡](../outputs/adaptive-d1-optimizer-benchmark/traces.csv)、[摘要](../outputs/adaptive-d1-optimizer-benchmark/summary.csv)、[收斂圖](../outputs/adaptive-d1-optimizer-benchmark/convergence.svg)。

下一步不是訓練深度模型：現有可用影像不足 50 張。應先建立可重現的 30/10/10 不重疊影像資料集，再以每張圖的 Grid label 訓練可解釋 feature-based selector，並保留 infeasible 標記。
