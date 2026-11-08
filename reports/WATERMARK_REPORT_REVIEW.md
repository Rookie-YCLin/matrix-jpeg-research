# 浮水印報告審閱紀錄

依 [Issue #6](https://github.com/Rookie-YCLin/matrix-jpeg-research/issues/6) 查核交件規格。其原題名屬舊研究，最新確認的研究方向為blind_watermark 的 SVD 區塊改良及其 JPEG 抗壓縮能力驗證。封面沿用已確認的姓名、學號。學校、系級、授課教師、繳交日期待填，與授課教師確認正式題名待辦。

| 項目 | 此版核對結果 |
|---|---|
| PDF、A4、單欄 | 已匯出獨立 PDF；pdfinfo 確認 595.28 × 841.89 pt；逐頁目視單欄 |
| 正文 | LaTeX 明訂 12bp（PDF 的 12 pt） |
| 字型 | pdffonts 確認 DFKaiShu-SB-Estd-BF、TimesNewRomanPSMT、TimesNewRomanPS-BoldMT 均嵌入；pdffonts 的所有字型列均為 emb=yes，數學使用 LaTeX 數學字型 |
| 頁數 | 9 頁審閱稿；正式版需至少 10 頁，最終候選驗證及第 4、5 章補齊後再驗收，不加空白頁 |
| 公式及版面 | 全頁渲染核對封面、章節、公式、表格及引用；日誌無缺字、超寬或未解析引用。數學字型有尺寸替代提示 |
| 結果 | 第四章最終方法與第五章結果及結論保留待定 |

## 撰寫與證據取捨

保留已完成的緒論、數位浮水印、JPEG、SVD、原版演算法與配對實驗方法。正文集中於最終選定的方法與完整預定測試條件。G5 前置診斷可提供選擇依據，正式比較前須固定候選與測試條件，並交代診斷樣本與正式驗證樣本是否重疊。報告逐條件呈現原版及候選的 BER、PSNR 與限制，保留直接影響選擇、適用條件或結論的負面證據。若未取得正向結果，依實測撰寫結論。

探索性研究的程式、CSV、manifest 及重跑證據留在原 PR 與固定提交。上一版報告對 G3 軟判決的推導仍可在本 PR 前版追溯。

- [G2 d2 探索與固定證據](https://github.com/Rookie-YCLin/matrix-jpeg-research/pull/17)，`cb8b5d89c3548a504d6d40f57857537c4f20c06c`。主要 Q10 未觀察到相近品質下的 BER 改善。
- [G3 軟判決與固定證據](https://github.com/Rookie-YCLin/matrix-jpeg-research/pull/18)，`e5ac1d82282bd20d708f2337ec4642a67bfbc3cd`。主要 Q10 未達改善目標。
- [G4 第一奇異值硬判決與固定證據](https://github.com/Rookie-YCLin/matrix-jpeg-research/pull/20)，`f8fc1de587901f5fd73bffd7f79ddf5d65d4e16a`。主要 Q10 未達改善目標，Q20 的群方向反轉仍有觀察紀錄。

## 本版逐頁核對與待填內容

以 Poppler 將最終 PDF 全部九頁渲染為 PNG。第 1 頁核對題名與摘要，第 2–4 頁核對緒論、JPEG、指標與 SVD 公式，第 5–6 頁核對上游演算法、融合分群及換序不等式，第 7–8 頁核對診斷數字、實驗條件及重跑指令，第 9 頁核對第四、第五章保留欄及引用。首次渲染發現重跑命令溢出，改為分行後再修正命令空格。最終日誌無超寬、缺字或未解析引用。

[PR #21 固定診斷](https://github.com/Rookie-YCLin/matrix-jpeg-research/blob/9a08fcdfba64a51a8034f3b82abbf2c5e817a014/watermark_baseline/MECHANISM.md) 的 57 及 2,027 是對角值排序事件，以 29,754 個通道區塊為分母。兩個手算案例來自原版公式，屬教學推導。此證據沒有驗證保序候選的 JPEG BER。

- 第四章補上最終候選的版本、公式、可行條件及平手規則，說明與原版的差異、盲擷取設定、選擇依據及事前判準。
- 第五章補上無攻擊與全部預定 JPEG 條件的逐圖和總計 BER、錯誤數與分母、嵌入及 JPEG PSNR、配對差值與失敗案例。交代資料重疊、適用限制、負面證據及結論。
- 補列實測提交、原始 CSV、manifest、版本、雜湊、重跑命令與驗收紀錄。依實測更新摘要，再核對封面、至少十頁及完整 PDF 版面。

在已安裝 Windows 標楷體及 Times New Roman 的環境，從根目錄執行兩次：

```powershell
xelatex -interaction=nonstopmode -halt-on-error -output-directory=reports reports/WATERMARK_REPORT.tex
pdfinfo reports/WATERMARK_REPORT.pdf
pdffonts reports/WATERMARK_REPORT.pdf
```

正式版完成後，再渲染並逐頁核對結果、頁數及字型。
