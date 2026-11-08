# 專案工作規範

- 開工先讀 [正式規格](PROJECT_SPEC.md)、[Codex 交接](docs/CODEX_NEXT_SESSION.md)、[實驗索引](docs/EXPERIMENT_INDEX.md) 和 `PROGRESS.md`，核對程式、測試、輸出與 [Issue #8](https://github.com/Rookie-YCLin/matrix-jpeg-research/issues/8) 的正式方向。
- 現行研究只修改 `blind_watermark` 的 SVD 區塊演算法，JPEG 作黑盒攻擊。W0、W0-D 與 G2 是已交付的基準、診斷與參數探索。G3 的候選方法及實測見 [PR #18](https://github.com/Rookie-YCLin/matrix-jpeg-research/pull/18)，待人工驗收；未授權前不得另開候選或重跑調參。
- 使用 Python 3.13 隔離環境和鎖定依賴。保存來源、雜湊、版本、命令、CSV 與驗證證據。圖表源自實際 CSV，每個里程碑更新 `PROGRESS.md`。測試失敗須保留日誌、診斷並重跑。
- 保留已驗證的程式、資料、測試、歷史 PR 及 Research CI。使用獨立分支和新輸出目錄。禁止直接修改 main、自動合併或啟用 AI 自動審查。合併須經研究主持人批准。
