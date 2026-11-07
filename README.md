# Matrix JPEG Research｜研究室入口

研究者於 2026-11-08 正式批准《基於 SVD 秩一分解與區塊 DCT 頻譜之 JPEG 壓縮穩定性分析》。[Issue #11](https://github.com/Rookie-YCLin/matrix-jpeg-research/issues/11) 是 Codex 唯一有效的新實驗工作包。[Issue #8](https://github.com/Rookie-YCLin/matrix-jpeg-research/issues/8) 保存正式決策，[Issue #10](https://github.com/Rookie-YCLin/matrix-jpeg-research/issues/10) 的舊 W0/G1 浮水印工作包已暫緩。禁止執行舊浮水印工作、嵌入／擷取開發及 BER 實驗。R2 暫緩。

先讀[一週研究章程](docs/ONE_WEEK_RESEARCH_CHARTER.md)與 [Codex 交接卡](docs/CODEX_NEXT_SESSION.md)。這些管理文件目前位於 [Draft PR #9](https://github.com/Rookie-YCLin/matrix-jpeg-research/pull/9) 的規劃分支。實驗從最新 `origin/main` 另開分支。

## 既有研究基線

`PROJECT_SPEC.md`、`PROGRESS.md` 與 `reports/` 保存已驗收的全圖 SVD、低秩誤差及固定原圖方向投影研究。`data/README.md` 記錄影像來源，`outputs/run-m2/` 保存四種品質的 JPEG、解碼圖、CSV 與執行紀錄。

保留 `main` 的 `PROJECT_SPEC.md`、`experiment.py`、既有 13 項測試、`outputs/run-m2/` 及歷史 CSV。[PR #7](https://github.com/Rookie-YCLin/matrix-jpeg-research/pull/7) 保持開啟、未合併，分支與內容完整保留。禁止直接修改 `main` 或自動合併 PR。

舊版 G0=A 與 W0/G1 章程保存在 [PR #9 的前版提交](https://github.com/Rookie-YCLin/matrix-jpeg-research/tree/070110609d11f6b7ed25d820e87bf7a020bc02fb)，僅供追溯。
