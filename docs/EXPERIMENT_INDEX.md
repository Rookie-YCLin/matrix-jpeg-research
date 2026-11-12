> 2026-11-12 後續：矩陣裕度方案d1=720在QF5–95每5點均0/32，但PNG PSNR僅15.56 dB；保留獨立高失真候選，不替換G6。見[驗證報告](../reports/MATRIX_MARGIN_LOW_QF.md)。

## 2026-11-12 論文導向低 QF（負結果）

[報告](../reports/PAPER_LOW_QF_FINDINGS.md) · [事前方案](PAPER_LOW_QF_PLAN.md) · [首輪CSV](../outputs/paper-low-qf-initial/results.csv) · [追加CSV](../outputs/paper-low-qf-nearest/results.csv)。三候選QF5均32/32，未修復，保留G6。

# 實驗索引

## G6｜已達標的 SVD QIM 步長改良

- 固定 QF15 原版 **32/32** 錯，改良 d1=90、d2=20 **0/32** 錯；**相對 BER 降幅 100%**，符合事先設定的 ≥10% 優秀門檻。
- 改良只改第一奇異值量化步長；上游 DWT／DCT／洗牌／K-means 不變。完整曲線測得 QF5 退步；不能宣稱所有 QF 改善。
- [方法與數學說明](../reports/G6_SVD_QIM_QF15_SUCCESS.md) · [第一輪15候選CSV](../outputs/svd-qim-qf15-exploration/results.csv) · [完整驗證CSV](../outputs/svd-qim-qf15-selected/results.csv) · [驗證CI](https://github.com/Rookie-YCLin/matrix-jpeg-research/actions/runs/42463429539) · [PR #25](https://github.com/Rookie-YCLin/matrix-jpeg-research/pull/25)。

---


## W1｜指定原圖之上游 BER–QF 基準

- [PR #24](https://github.com/Rookie-YCLin/matrix-jpeg-research/pull/24) · [實際 GitHub Actions 執行](https://github.com/Rookie-YCLin/matrix-jpeg-research/actions/runs/42461739759) · [CSV](../outputs/ori-qf-scan/results.csv) · [manifest](../outputs/ori-qf-scan/manifest.json) · [實驗摘要](../outputs/ori-qf-scan/README.md)。
- 唯一來源為上游 `examples/pic/ori_img.jpeg`，固定原版 SVD、32-bit payload、Pillow JPEG RGB／4:4:4，QF=5～95、每 5 一點。僅評估 BER。
- 最高 BER：QF15、20 均 **32/32（100%）**；依事先規則 **x=15**。QF5 12/32、QF10 1/32、QF25～95 全為 0/32；未攻擊 PNG 0/32。
- QF15、20 解出向量均恰好是原始 payload 的互補值；這是值得後續驗證的極性反轉線索，不能直接當成 SVD 抗壓改善。
- 改善驗收在 x=15：相對降幅 R≥5% 對應候選錯誤 ≤30/32，R≥10% 對應 ≤28/32。**這是原版基準，不是改良結果。**
- 以下 W0–G5 是先前不同三圖實驗，不能混作此指定圖的比較。

---

固定版本連結可在 PR 合併前讀取。CI 成功為技術驗收，主持人負責研究驗收。

## W0｜原版基準

- 提交 `f5a47fc1ba40cc35f5794648b4440cb1fed782d1` · [PR #13](https://github.com/Rookie-YCLin/matrix-jpeg-research/pull/13) · [CI](https://github.com/Rookie-YCLin/matrix-jpeg-research/actions/runs/42418341821) · [18 項本機測試](https://github.com/Rookie-YCLin/matrix-jpeg-research/blob/f5a47fc1ba40cc35f5794648b4440cb1fed782d1/outputs/pytest-w0.txt)
- [輸入來源與 SHA](https://github.com/Rookie-YCLin/matrix-jpeg-research/blob/f5a47fc1ba40cc35f5794648b4440cb1fed782d1/data/w0/inputs.json) · [逐位 CSV](https://github.com/Rookie-YCLin/matrix-jpeg-research/blob/f5a47fc1ba40cc35f5794648b4440cb1fed782d1/outputs/run-w0/results.csv) · [manifest](https://github.com/Rookie-YCLin/matrix-jpeg-research/blob/f5a47fc1ba40cc35f5794648b4440cb1fed782d1/outputs/run-w0/manifest.json) · [重跑比對](https://github.com/Rookie-YCLin/matrix-jpeg-research/blob/f5a47fc1ba40cc35f5794648b4440cb1fed782d1/outputs/w0-replay-comparison.json)
- 三張 RGB 圖、一個 32-bit payload，d1=36、d2=20。無攻擊 PNG 與各 Q40/60/80/95 皆為 0/96；此樣本存在 BER 下限，無法據此宣稱普遍零 BER。4:4:4 與 codec 版本限制外推。

## W0-D｜壓力診斷

- 提交 `168e5070cacbdeeaefab58ed469dd7e90db4aa3f` · [PR #14](https://github.com/Rookie-YCLin/matrix-jpeg-research/pull/14) · [CI](https://github.com/Rookie-YCLin/matrix-jpeg-research/actions/runs/42450322328) · [21 項本機測試](https://github.com/Rookie-YCLin/matrix-jpeg-research/blob/168e5070cacbdeeaefab58ed469dd7e90db4aa3f/outputs/pytest-w0-d.txt)
- [逐位 CSV](https://github.com/Rookie-YCLin/matrix-jpeg-research/blob/168e5070cacbdeeaefab58ed469dd7e90db4aa3f/outputs/run-w0-d/results.csv) · [診斷分數](https://github.com/Rookie-YCLin/matrix-jpeg-research/blob/168e5070cacbdeeaefab58ed469dd7e90db4aa3f/outputs/run-w0-d/decision_scores.csv) · [manifest](https://github.com/Rookie-YCLin/matrix-jpeg-research/blob/168e5070cacbdeeaefab58ed469dd7e90db4aa3f/outputs/run-w0-d/manifest.json) · [重跑比對](https://github.com/Rookie-YCLin/matrix-jpeg-research/blob/168e5070cacbdeeaefab58ed469dd7e90db4aa3f/outputs/w0-d-replay-comparison.json)
- 沿用 W0 存檔 PNG。4:4:4 的 Q10、20、30 分別為 12/96、78/96、0/96；4:2:0 的 Q40、60、80 皆 0/96。Q 與錯誤率在此樣本非單調。Q20 的 coffee 為 32/32，保留原版判決。診斷分數只作解釋，未取代公開 bit API。

### W0 與 W0-D 重跑

在相應固定提交的獨立工作樹及 Python 3.13 隔離環境執行。所有輸出目錄都須是新目錄。W0-D 使用其提交所含的原始 W0 存檔，重跑 W0 的新目錄只供比對。跨平台保留 codec 版本及差異。

```text
python -m pip install -r requirements-w0.txt
python -m pip install --no-build-isolation -r watermark_baseline/upstream.txt
python -m pip check
python -m watermark_baseline --output-dir outputs/run-w0-review
python -m watermark_baseline --output-dir outputs/run-w0-review-repeat
python -m watermark_baseline.compare_runs outputs/run-w0-review outputs/run-w0-review-repeat
python -m pytest -v
```

在 W0-D 提交另執行：

```text
python -m watermark_baseline.stress --output-dir outputs/run-w0-d-review
python -m watermark_baseline.stress --output-dir outputs/run-w0-d-review-repeat
python -m watermark_baseline.compare_runs outputs/run-w0-d-review outputs/run-w0-d-review-repeat
```

## G2｜已交付的 d2 參數探索

- 提交 `cb8b5d89c3548a504d6d40f57857537c4f20c06c` · [PR #17](https://github.com/Rookie-YCLin/matrix-jpeg-research/pull/17) · [CI](https://github.com/Rookie-YCLin/matrix-jpeg-research/actions/runs/42451892505) · [逐位 CSV](https://github.com/Rookie-YCLin/matrix-jpeg-research/blob/cb8b5d89c3548a504d6d40f57857537c4f20c06c/outputs/run-g2/results.csv) · [配對 CSV](https://github.com/Rookie-YCLin/matrix-jpeg-research/blob/cb8b5d89c3548a504d6d40f57857537c4f20c06c/outputs/run-g2/paired.csv) · [manifest](https://github.com/Rookie-YCLin/matrix-jpeg-research/blob/cb8b5d89c3548a504d6d40f57857537c4f20c06c/outputs/run-g2/manifest.json) · [限制與重跑](https://github.com/Rookie-YCLin/matrix-jpeg-research/blob/cb8b5d89c3548a504d6d40f57857537c4f20c06c/watermark_baseline/G2.md)
- 主要 Q10 未觀察到相近品質下的改善。採用交付實驗的 1.0 dB 操作門檻，與 Issue #16 草擬的 0.5 dB 建議分開，人工驗收時核對事前凍結紀錄。

## G3｜已交付的 SVD 區塊軟判決

- 提交 `e5ac1d82282bd20d708f2337ec4642a67bfbc3cd` · [PR #18](https://github.com/Rookie-YCLin/matrix-jpeg-research/pull/18) · [CI](https://github.com/Rookie-YCLin/matrix-jpeg-research/actions/runs/42453089827) · [逐位 CSV](https://github.com/Rookie-YCLin/matrix-jpeg-research/blob/e5ac1d82282bd20d708f2337ec4642a67bfbc3cd/outputs/run-g3/results.csv) · [manifest](https://github.com/Rookie-YCLin/matrix-jpeg-research/blob/e5ac1d82282bd20d708f2337ec4642a67bfbc3cd/outputs/run-g3/manifest.json) · [限制與重跑](https://github.com/Rookie-YCLin/matrix-jpeg-research/blob/e5ac1d82282bd20d708f2337ec4642a67bfbc3cd/watermark_baseline/G3.md)
- 同一批 W0/W0-D 封存影像。主要 Q10 由 12/96 變為 13/96，未達改善目標。實測已交付，研究驗收仍待主持人確認。


## R1｜歷史方向

- 提交 `61f30007860c401394367c31721473c18625b254` · [PR #12](https://github.com/Rookie-YCLin/matrix-jpeg-research/pull/12) · [CI](https://github.com/Rookie-YCLin/matrix-jpeg-research/actions/runs/42415889499) · [27 項本機測試](https://github.com/Rookie-YCLin/matrix-jpeg-research/blob/61f30007860c401394367c31721473c18625b254/outputs/r1-pytest.txt)
- [CSV](https://github.com/Rookie-YCLin/matrix-jpeg-research/blob/61f30007860c401394367c31721473c18625b254/outputs/run-r1/sensitivity.csv) · [manifest](https://github.com/Rookie-YCLin/matrix-jpeg-research/blob/61f30007860c401394367c31721473c18625b254/outputs/run-r1/manifest.json) · [頻譜權重](https://github.com/Rookie-YCLin/matrix-jpeg-research/blob/61f30007860c401394367c31721473c18625b254/outputs/run-r1/weights.npy) · [重跑比對](https://github.com/Rookie-YCLin/matrix-jpeg-research/blob/61f30007860c401394367c31721473c18625b254/outputs/r1-replay-comparison.json)
- 單張灰階影像、四組既有 JPEG 表格與 SVD 頻譜量，重複奇異值子空間的個別方向依基底而定。無浮水印或 BER 證據。R2 暫緩。

在固定提交用 Python 3.13 安裝 `requirements.txt`，PowerShell 設定 `$env:OPENBLAS_NUM_THREADS='1'`，再以新目錄和新比對檔重跑。

```text
python -m analysis.r1 --input data/ascent.png --jpeg-dir outputs/run-m2 --output-dir outputs/run-r1-local
python -m analysis.r1 --input data/ascent.png --jpeg-dir outputs/run-m2 --output-dir outputs/run-r1-local-replay
python -m analysis.compare_r1 outputs/run-r1-local outputs/run-r1-local-replay --report outputs/r1-local-comparison.json
python -m pytest -v
```

既有 M0–M4、M2 封存輸出與 [PR #7 PDF](https://github.com/Rookie-YCLin/matrix-jpeg-research/pull/7) 保留。[PR #15](https://github.com/Rookie-YCLin/matrix-jpeg-research/pull/15) 保留無金鑰審查驗證及設計，AI 正式模式暫不啟用。
