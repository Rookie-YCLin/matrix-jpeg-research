# 專案工作規範

- 先讀 [Issue #8 決議](https://github.com/Rookie-YCLin/matrix-jpeg-research/issues/8)、[Issue #10 原版基準](https://github.com/Rookie-YCLin/matrix-jpeg-research/issues/10)、[PROJECT_SPEC.md](PROJECT_SPEC.md)、[Codex 交接卡](docs/CODEX_NEXT_SESSION.md) 與 `PROGRESS.md`，核對程式、測試及實際輸出。Draft PR #9 存放管理規格，實驗從最新 `origin/main` 開獨立分支。
- 首個任務是原版 W0／G1，使用固定提交、d1=36、d2=20 與原版 bit 擷取。G2 在基準成功、可重現且經研究審查後獨立進行。JPEG 僅作黑盒攻擊。
- 保留 `experiment.py`、13 項既有測試、`outputs/run-m2/`、歷史 CSV、PR #7 與 PR #12。禁止直接修改 `main` 或自動合併 PR。
- 使用 Python 3.13 隔離環境和鎖定依賴。圖表源自實際 CSV。保留來源、雜湊、版本、命令及驗證證據，每個里程碑更新 `PROGRESS.md`。
- Research CI 沿用既有 M2 存檔和暫存重跑驗收。於 Checks 核對依賴安裝與 `python -m pytest -v` 逐項結果。失敗保留日誌，在原 PR 分支診斷、修正、重跑與推送。PR 以繁中記錄變更、結果、測試、資料位置、限制與待審事項。
