# 專案工作規範

- 先讀 [PROJECT_SPEC.md](PROJECT_SPEC.md)、[實驗索引](docs/EXPERIMENT_INDEX.md)、[Codex 交接](docs/CODEX_NEXT_SESSION.md) 與 `PROGRESS.md`，核對實際程式、測試及輸出。正式研究決策以 [Issue #8](https://github.com/Rookie-YCLin/matrix-jpeg-research/issues/8) 為準。
- [Issue #10](https://github.com/Rookie-YCLin/matrix-jpeg-research/issues/10) 是 W0 和 W0-D 的基準驗收來源。G2 唯一工作入口是 [Issue #16](https://github.com/Rookie-YCLin/matrix-jpeg-research/issues/16)，須先獲主持人批准。JPEG 只作黑盒攻擊。
- 保留歷史程式、測試、資料和輸出，以及 PR #7、#12、#13、#14、#15。實驗使用獨立分支與新輸出目錄。禁止直接修改 main、自動合併或啟用 AI 審查。
- 使用 Python 3.13 隔離環境和鎖定依賴。保留來源、雜湊、版本、重跑命令、CSV 與驗證證據。圖表源自實際 CSV，每個里程碑更新 `PROGRESS.md`。
- 保留 Research CI 的 M2 驗收及後續已整合的 W0、W0-D 重跑。於 Checks 查閱依賴和逐項測試。失敗保留日誌、診斷、修正後重跑。PR 以繁中記錄變更、結果、證據、限制與待審事項。
