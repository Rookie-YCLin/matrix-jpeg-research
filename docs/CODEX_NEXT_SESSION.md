# Codex 下一次工作階段｜只執行 Issue #11 的 R1

研究者於 2026-11-08 正式批准《基於 SVD 秩一分解與區塊 DCT 頻譜之 JPEG 壓縮穩定性分析》。[Issue #11](https://github.com/Rookie-YCLin/matrix-jpeg-research/issues/11) 是 Codex 唯一有效的新實驗工作包。[Issue #8](https://github.com/Rookie-YCLin/matrix-jpeg-research/issues/8) 保存正式決策，[Issue #10](https://github.com/Rookie-YCLin/matrix-jpeg-research/issues/10) 的舊 W0/G1 浮水印工作包已暫緩。禁止執行舊浮水印工作、嵌入／擷取開發及 BER 實驗。R2 暫緩。

## 開工與環境

先讀 Issue #11 全文，再核對 `PROJECT_SPEC.md`、`PROGRESS.md`、程式、測試與既有輸出。這份交接仍在 [Draft PR #9](https://github.com/Rookie-YCLin/matrix-jpeg-research/pull/9)，前 4 行只讀取文件。工作樹須乾淨，且尚未有 R1 分支，才執行下列建立分支命令。若已有 R1 分支，先核對其來源與現有改動，再接續。保護使用者的本地變更。

```powershell
git fetch origin
git show origin/planning/watermark-7day-charter:docs/CODEX_NEXT_SESSION.md
git show origin/planning/watermark-7day-charter:docs/ONE_WEEK_RESEARCH_CHARTER.md
git show origin/planning/watermark-7day-charter:AGENTS.md
git status --short
git switch -c codex/r1-svd-dct-sensitivity origin/main
py -3.13 -m venv .venv-r1
$python = '.\.venv-r1\Scripts\python.exe'
& $python -m pip install -r requirements.txt
& $python -m pip check
& $python -m pytest -v
```

## 實作後驗收

在 `analysis/` 實作 Issue #11 的數學、量化表讀取及輸出。先確認 Pillow 排列與灰階分量表 ID。若來源不齊，先回報並依 Issue #11 記錄同設定重建方法。新增獨立測試，完成下列兩次執行，再比較數值與表格並保留容差與差異。兩個輸出路徑都須是新目錄。

```powershell
& $python -m analysis.r1 --input data/ascent.png --jpeg-dir outputs/run-m2 --output-dir outputs/run-r1
& $python -m analysis.r1 --input data/ascent.png --jpeg-dir outputs/run-m2 --output-dir outputs/run-r1-replay
& $python -m pytest -v
```

保存來源、雜湊、版本、四張實際量化表、CSV、Wᵢ 及檢查證據，更新 `PROGRESS.md`。提交、推送 R1 分支並開 PR，附重跑命令、SHA、CI 與限制，等待研究審查。

保留 `main` 的 `PROJECT_SPEC.md`、`experiment.py`、既有 13 項測試、`outputs/run-m2/` 及歷史 CSV。[PR #7](https://github.com/Rookie-YCLin/matrix-jpeg-research/pull/7) 保持開啟、未合併，分支與內容完整保留。禁止直接修改 `main` 或自動合併 PR。
