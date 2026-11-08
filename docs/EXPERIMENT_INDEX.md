# 實驗索引

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

## G2｜待批准

[Issue #16](https://github.com/Rookie-YCLin/matrix-jpeg-research/issues/16) 為唯一入口。預計分支 `codex/g2-d2-paired`。提交、PR、CSV、manifest、CI 與實驗重跑命令待交付後補入。建議主比較為 Q10／4:4:4，Q20 作高壓診斷，Q30 作低錯誤對照。PSNR 門檻須在看 G2 結果前核定。三張影像、單一 payload，每條件 96 位元。

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
