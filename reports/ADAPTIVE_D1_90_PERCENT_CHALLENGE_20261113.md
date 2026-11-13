# 90% 命中率挑戰：單圖達標與過度擬合檢驗（2026-11-13）

## 實驗範圍
PR #39 的單張主圖，已量測的 d1=1..150 Grid oracle，Model B J*=0.044210042965582494、d1*=33。**沒有新的 JPEG 測量**。200 seeds、24 個不重複 objective 查詢，使用 Grid lookup replay。

對固定/分層初始化、粗搜點數 n=4/6/8/10/12、區域數 k=1/2/3、區域最小距離 5/10/20、鄰域抽樣寬度 1/3/7 做 270 組組合掃描。**這是同圖超參數搜尋，不是測試集**。

## 單圖 90% 目標
- 舊版：n=10 固定粗搜，鄰域寬度 7，24 evaluations：52/200=26% 命中。
- 新版：n=8 固定粗搜、k=1、width=1，24 evaluations：200/200=100% 命中，mean J=J*=0.044210042965582494。
- 由於 width=1 且粗搜固定，該方法基本上是**決定性**的：200 個 seed 的結果並非 200 次獨立隨機成功證據。不能對 100% 做二項式成功率推論。

## 對目標函數變化的反證測試
在相同 Grid 資料上更改 objective（不是新圖）：
- 原 Model B：n=8/k=1/width=1 命中 200/200，oracle d1=33。
- mean BER only：命中 200/200，oracle d1=140（其他零 BER d1 也可能並列）。
- worst BER only：命中 200/200，oracle d1=140（可能並列）。
- quality threshold=35dB 的 0.5 mean BER + 0.5 畫質懲罰：命中 200/200，oracle d1=41。
- risk mix 0.25 mean BER + 0.25 worst BER + 0.5 PSNR40dB 懲罰：**命中 0/200**，oracle d1=41。

這證明在原圖達成 100% 不能保證換一個研究目標後仍成功；更不能推論未見影像 90% 命中。

## 研究建議
1. 將這張圖標記為**已用於調參的開發圖**，不得當獨立測試。
2. 90% 必須定義為「固定 budget、固定 objective，在未見影像中達到 Grid oracle 或在容忍 regret ε 內」的比例；對平手 oracle 使用 objective equality，不以特定 d1 判定。
3. 真正成本：24 個候選 x 6 個 QF JPEG BER + PSNR；記錄 wall time。不可用 200 次 lookup 回放代替 200 張影像。
4. 預先指定 n=8/width=1 與 n=10/width=7、分層隨機版三種候選；在新的驗證圖上比較，不再在同一張圖無限制掃參。
5. 如無法取得完整 150-point 新圖 oracle，先定義可重現的高預算 reference search；必須將「達到 reference」與「真正全域最佳」分開報告。

## 重現
`python experiments/adaptive_d1_nearest_replay.py outputs/adaptive-d1-grid-qf5-qf10-d1-1-150/per_d1.csv --budget 24 --trials 200`

程式已提交；本輪數值來自 GitHub CSV 的 JavaScript 實際 lookup 計算，尚待完整 Python 環境驗證。
