# 浮水印報告審閱紀錄

依 [Issue #6](https://github.com/Rookie-YCLin/matrix-jpeg-research/issues/6) 查核交件規格。其原題名屬舊研究，最新確認的研究方向為盲式浮水印與區塊軟判決。封面沿用已確認的姓名、學號。學校、系級、授課教師、繳交日期待填，與授課教師確認正式題名待辦。

| 項目 | 此版核對結果 |
|---|---|
| PDF、A4、單欄 | 已匯出獨立 PDF；pdfinfo 確認 595.28 × 841.89 pt；逐頁目視單欄 |
| 正文 | LaTeX 明訂 12bp（PDF 的 12 pt） |
| 字型 | pdffonts 確認 DFKaiShu-SB-Estd-BF、TimesNewRomanPSMT、TimesNewRomanPS-BoldMT 均嵌入；數學使用 LaTeX 數學字型 |
| 頁數 | 6 頁審閱稿；正式版需至少 10 頁，G3 資料到齊後再驗收，不加空白頁 |
| 公式及版面 | 全頁渲染核對封面、章節、公式、表格及引用；日誌無缺字、超寬或未解析引用。數學字型有尺寸替代提示 |
| 結果 | 依本次範圍保留 G3 結果章待填，沒有 G3 BER、PSNR 或改良結論 |

來源核對以 GitHub 上游固定提交及 W0、W0-D、G2 的提交連結為準。軟判決核對固定提交 `318eed431eca0d106805d0b1fa05dc5110272ea8` 的 `watermark_baseline/soft_decision.py`。報告撰寫期間，[G3 Draft PR #18](https://github.com/Rookie-YCLin/matrix-jpeg-research/pull/18) 已交付實測。其提交 `e5ac1d82282bd20d708f2337ec4642a67bfbc3cd` 使用 W0 與 W0-D 的封存檔案。依本次交付範圍保留結果章，後續以固定版本的 CSV、manifest 與重跑證據填寫。

在已安裝 Windows 標楷體及 Times New Roman 的環境，從根目錄執行兩次：

```powershell
xelatex -interaction=nonstopmode -halt-on-error -output-directory=reports reports/WATERMARK_REPORT.tex
pdfinfo reports/WATERMARK_REPORT.pdf
pdffonts reports/WATERMARK_REPORT.pdf
```

正式版完成後，再渲染並逐頁核對結果、頁數及字型。
