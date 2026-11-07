# Codex 交接｜執行 Issue #10 的原版浮水印基準

先讀 [Issue #10](https://github.com/Rookie-YCLin/matrix-jpeg-research/issues/10) 及 [研究決議](https://github.com/Rookie-YCLin/matrix-jpeg-research/issues/8)。從 Draft PR #9 的規劃分支讀正式規格，從最新 `origin/main` 建立實驗分支。先核對 `PROGRESS.md`、現有程式、測試及輸出。下列建立分支命令以工作樹乾淨且分支尚未建立為前提。

```powershell
git fetch origin
git show origin/planning/watermark-7day-charter:AGENTS.md
git show origin/planning/watermark-7day-charter:PROJECT_SPEC.md
git show origin/planning/watermark-7day-charter:docs/ONE_WEEK_RESEARCH_CHARTER.md
git show origin/planning/watermark-7day-charter:docs/CODEX_NEXT_SESSION.md
git status --short
git switch -c codex/w0-watermark-baseline origin/main
py -3.13 -m venv .venv-w0
$python = '.\.venv-w0\Scripts\python.exe'
& $python -m pip install -r requirements.txt
& $python -m pip check
& $python -m pytest -v
```

固定上游提交 `322c90dc02d45644692095b34d3a6b735b6edbd8`。在 W0 分支另建鎖定依賴清單，確認 Python 3.13 相容，保存 OpenCV、PyWavelets、NumPy、Pillow、JPEG codec 和上游 SHA。先凍結輸入 manifest，再在 `watermark_baseline/` 包裝上游公開介面。新增獨立測試與新輸出目錄，保留歷史資料。

依 Issue #10 完成無攻擊驗證，再執行四組黑盒 JPEG 攻擊並重跑。交付逐位證據、CSV、manifest、確切重跑命令與 `python -m pytest -v` 結果，更新 `PROGRESS.md` 並開 W0 PR 待審。G2 在基準成功、可重現且通過審查後另開。
