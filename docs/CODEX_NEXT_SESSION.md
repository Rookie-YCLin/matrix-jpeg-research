# Codex 交接｜Issue #16

唯一 G2 工作入口為 [Issue #16](https://github.com/Rookie-YCLin/matrix-jpeg-research/issues/16)。先確認主持人已驗收 W0、確認 W0-D 證據、核准比較設計並在該 Issue 明確放行。核對 [正式規格](../PROJECT_SPEC.md)、[實驗索引](EXPERIMENT_INDEX.md) 和 `PROGRESS.md`。目前本機已有 codex/g2-d2-comparison 與未提交的工作。先保留並核對其基底、內容、執行條件與驗收門檻，獲准後才接續，避免另起一套。下列 git switch -c 只適用於分支不存在且工作樹乾淨的環境，並須確認最新 main 已含驗收的 W0 與 W0-D。

```powershell
git fetch origin
git status --short
git switch -c codex/g2-d2-comparison origin/main
py -3.13 -m venv .venv-g2
$python = '.\.venv-g2\Scripts\python.exe'
& $python -m pip install -r requirements-w0.txt
& $python -m pip install --no-build-isolation -r watermark_baseline/upstream.txt
& $python -m pip check
& $python -m pytest -v
```

若主持人明確准許合併前開工，改用 Issue #16 指定的 #14 固定提交，先以 W0-D 分支作為 G2 PR base。不得從缺 W0 或 W0-D 的 main 開始實驗。依 Issue 驗收，保存逐位 CSV、manifest、重跑命令、回歸測試與報告。只新增 G2 專用輸出，既有資料及 AI 審查部署保持原狀。
