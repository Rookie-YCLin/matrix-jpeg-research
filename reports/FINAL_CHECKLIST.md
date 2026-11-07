# 最終核對紀錄｜階段 II

- [x] [正式 PDF](FINAL_REPORT.pdf) 實測 11 頁 A4、單欄、正文 12 pt。嵌入標楷體與 Times New Roman。公式使用相容數學字型。
- [x] 完成 [逐頁檢查與縮圖](pdf-review/REVIEW.md)、[字型清單](pdf-review/pdffonts.txt) 及 CSV 引值核對。交付 PDF SHA-256 為 `b3ad3c0f312ab52b638d6f4c8b297230a5d732baef1ba19f9eda00f15857b379`。
- [x] Figure 1 的原始灰階與差值映射分開，Q=60 與 Q=80 的精確值移到表 2。見 [圖說及來源](figure-1/CAPTION.md)。
- [x] 沿用 M2 存檔與已驗收研究結論。回歸測試 `python -m pytest -v` 為 13 通過、0 失敗、0 跳過。GitHub 另見 PR Checks。
- [ ] 學校／系級、授課教師與繳交日期待填。PR #7 待使用者與外部審查批准。

## 重製

從專案根目錄執行。Python 使用原專案環境，Windows 需有標楷體、Times New Roman 與 XeLaTeX。三頁樣稿及其裁切仍保留作為階段 I 證據，正式 PDF 共用其 Rank-k 裁切。

```powershell
.\.venv\Scripts\python reports/draw_final_figures.py
.\.venv\Scripts\python reports/stage-i/draw_comparison.py
.\.venv\Scripts\python reports/figure-1/draw_figure1.py
xelatex -interaction=nonstopmode -halt-on-error -output-directory=reports reports/FINAL_REPORT.tex
xelatex -interaction=nonstopmode -halt-on-error -output-directory=reports reports/FINAL_REPORT.tex
pdfinfo reports/FINAL_REPORT.pdf
pdffonts reports/FINAL_REPORT.pdf
```

輸入 PNG、四份 M2 CSV 和原始解碼影像沿用已驗收存檔。完整實驗重現步驟在 PDF 附錄。
