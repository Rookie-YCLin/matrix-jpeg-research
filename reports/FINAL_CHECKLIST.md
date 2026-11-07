# M4 最終核對紀錄

## PR #7 重製版

正式題目依使用者定案為「JPEG 壓縮對影像奇異值與低秩結構之影響分析」。封面與 PDF metadata 已同步，姓名及學號為林易辰、B143012007。

- [x] [最終 PDF](FINAL_REPORT.pdf) 為 13 頁 A4。正文單欄 12 pt，章節與圖表自然分頁，封面後沒有硬斷頁指令。
- [x] `pdffonts` 證實標楷體與 Times New Roman 已嵌入。以 `pdftohtml -xml -zoom 1` 檢查兩種 12 pt 正文字型及文字邊界。公式使用相容數學字型。新圖的英文字及刻度使用 Times New Roman，圖像面板保留原始像素。
- [x] 以 `pdftoppm -r 112 -png` 渲染 13 頁，逐頁核對圖文、圖說、公式與分頁。詳見 [逐頁審查](pdf-review/REVIEW.md)及[字型原始清單](pdf-review/pdffonts.txt)。
- [x] 從 PDF 擷取表 2 的四列資料，逐列核對 M2 CSV 四捨五入。核對正文所引頻譜、能量與投影例子、8 張圖及 3 張表的編號。XeLaTeX 最終日誌未見缺字、超寬方框或未解析參照警告。
- [x] 本機 `python -m pytest -v` 為 13 通過、0 失敗、0 跳過。這是研究程式的回歸驗證。PDF 可讀性另以逐頁審查確認。
- [x] PDF SHA-256 為 `bc8edb299bf9111e0586c5066ab9eb397e95226557dfbaddc221ba7cb60544bc`。

## 重製方法

從專案根目錄執行。繪圖使用原有 Python 依賴和 Windows 本機的 Times New Roman，排版另需安裝標楷體及 XeLaTeX。儲存庫只保存生成的向量圖與報告，沒有字型檔。

```powershell
.\.venv\Scripts\python reports/draw_final_figures.py
xelatex -interaction=nonstopmode -halt-on-error -output-directory=reports reports/FINAL_REPORT.tex
xelatex -interaction=nonstopmode -halt-on-error -output-directory=reports reports/FINAL_REPORT.tex
pdfinfo reports/FINAL_REPORT.pdf
pdffonts reports/FINAL_REPORT.pdf
```

## 研究驗收與待確認

- [x] M4 研究內容已完成外部審查，PR #5 已合併。歷史重跑證據記於 [PROGRESS.md](../PROGRESS.md)。
- [x] 四份 M2 CSV、圖像和研究程式均沿用已驗收存檔。本輪從存檔重畫，裁切圖使用共同窗口。圖 4 下方是同秩誤差的百分點相減。
- [ ] 學校／系級、授課教師與繳交日期待填。
- [ ] PR #7 重製版待使用者逐頁驗收與批准。
