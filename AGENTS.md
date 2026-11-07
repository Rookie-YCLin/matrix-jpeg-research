# 專案工作規範

研究者於 2026-11-08 正式批准《基於 SVD 秩一分解與區塊 DCT 頻譜之 JPEG 壓縮穩定性分析》。[Issue #11](https://github.com/Rookie-YCLin/matrix-jpeg-research/issues/11) 是 Codex 唯一有效的新實驗工作包。[Issue #8](https://github.com/Rookie-YCLin/matrix-jpeg-research/issues/8) 保存正式決策，[Issue #10](https://github.com/Rookie-YCLin/matrix-jpeg-research/issues/10) 的舊 W0/G1 浮水印工作包已暫緩。禁止執行舊浮水印工作、嵌入／擷取開發及 BER 實驗。R2 暫緩。

- 開工先讀 Issue #11、[研究章程](docs/ONE_WEEK_RESEARCH_CHARTER.md)、[交接卡](docs/CODEX_NEXT_SESSION.md)、`PROJECT_SPEC.md` 與 `PROGRESS.md`，核對程式、測試與實際輸出。管理規格位於 Draft PR #9，R1 程式從最新 `origin/main` 另開分支。
- 保留 `main` 的 `PROJECT_SPEC.md`、`experiment.py`、既有 13 項測試、`outputs/run-m2/` 及歷史 CSV。[PR #7](https://github.com/Rookie-YCLin/matrix-jpeg-research/pull/7) 保持開啟、未合併，分支與內容完整保留。禁止直接修改 `main` 或自動合併 PR。
- 使用 Python 3.13 隔離環境和鎖定依賴。以 float64 分析，展示影像另行量化。
- 圖表源自實際輸出 CSV。保留輸入來源、雜湊、版本、命令及驗證證據。每個里程碑更新 `PROGRESS.md`。
- 保留原驗收標準。Research CI 在暫存目錄重跑 SVD 與 JPEG，核對 M2 已提交的 CSV、圖表輸入與必要檔案。存檔數據依保存的解碼 PNG 核對，runner 重跑依其實際 JPEG 解碼像素核對。
- 在 PR 的 Checks 查閱 Python、套件、JPEG codec 版本及 `python -m pytest -v` 逐項結果。依賴安裝失敗與 pytest 結果分開查閱。失敗時保留日誌，診斷、修正後重跑相同命令，在原 PR 分支推送。
- 以 PR 範本提供繁中驗收摘要，包含變更、結果、測試、資料位置、限制與待審查事項。CI 通過後等待外部研究審查及研究者合併批准。
