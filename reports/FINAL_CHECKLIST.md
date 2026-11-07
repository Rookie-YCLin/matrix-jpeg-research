# M4 最終核對紀錄

## 最終 PDF 驗收

- [x] [正式 PDF](FINAL_REPORT.pdf) 為 A4、10 頁、單欄。以 `pdfinfo` 查核頁數與尺寸，以 `pdftohtml -xml -zoom 1` 查核內文的 12 pt 字型及文字邊界，並逐頁確認正文為單欄。
- [x] `pdffonts` 列出標楷體 `DFKaiShu-SB-Estd-BF` 與 `TimesNewRomanPSMT`、`TimesNewRomanPS-BoldMT`、`TimesNewRomanPS-ItalicMT`。上述字型均為嵌入子集，並含 Unicode 對應（`emb/sub/uni = yes/yes/yes`）。本機字型族名確認為 DFKai-SB 與 Times New Roman。數學符號用相容數學字型，五張原始點陣圖的座標標籤為圖像的一部分。
- [x] 以 `pdftoppm -r 115 -png` 渲染全部頁面。逐頁檢查第 1 頁封面、第 2 頁摘要與動機、第 3 頁公式及證明、第 4 頁方法、第 5 頁表格與圖 1、第 6 頁圖 2 與 3、第 7 頁圖 4、第 8 頁投影公式與圖 5、第 9 頁結論與文獻、第 10 頁重現命令。修正附錄長雜湊換行後，重新檢查第 10 頁並確認前 9 頁渲染結果相同。
- [x] 從 PDF 擷取文字，核對姓名「林易辰」、學號 B143012007、M2 表格數據及原圖 SHA-256。學校／系級、教師及繳交日期仍留待填。
- [x] 交付 PDF 的 SHA-256 為 `cdbca8d11f3714a5893ffc0c8ce2e5be62302f85b99629ea389e64e95432c034`。如需修改封面，在專案根目錄用裝有指定字型的 Windows 執行 `xelatex -interaction=nonstopmode -halt-on-error -output-directory=reports reports/FINAL_REPORT.tex`，再重新核對 PDF。
- [x] 本次本機 `python -m pytest -v` 為 13 通過、0 失敗、0 跳過。遠端 Research CI 見本次 PDF PR 的 Checks。

**正式題目與授課教師確認：待使用者完成。**

## 已核對

- [x] [正式報告](FINAL_REPORT.md) 具封面欄位、中文摘要、數學推導、方法、結果、討論、結論、文獻及重現步驟。
- [x] [答辯稿](DEFENSE_NOTES.md) 涵蓋研究主線、公式、五張圖的讀法與八題問答。
- [x] 核對數學推導及適用條件。最佳性限秩至多 k 與 Frobenius 範數，零矩陣的相對誤差未定義。PSNR、解碼圖自身低秩誤差與固定方向投影各有明確基準。
- [x] 用 M2 的 [JPEG 指標](../outputs/run-m2/jpeg_metrics.csv)、[低秩誤差](../outputs/run-m2/rank_errors.csv)、[頻譜](../outputs/run-m2/spectrum.csv) 和 [投影](../outputs/run-m2/projections.csv) 核對公式、引用條件及四捨五入。
- [x] 五張圖均沿用 M2 存檔。核對圖號、相對路徑、圖說、座標軸與圖檔可讀性。學術與技術文獻連結已核對原始來源。
- [x] 本機 Windows 使用另一個已建立的 Python 3.13.14 隔離環境執行 `pip check`，依正式報告附錄的實驗命令重跑至新暫存目錄。原圖 SHA-256 與 JPEG 參數均與 M2 相符。
- [x] 四份重跑 CSV 的列索引與資料通過數值比對。各 JPEG、圖像、`jpeg_metrics.csv` 及 `spectrum.csv` 位元組一致。首次整批雜湊比對在 `projections.csv` 發現差異，逐檔核對後確認 `rank_errors.csv` 也有差異。兩者最大絕對差分別約 2.27e-13 與 1.07e-6（後者含未正規化平方誤差）。保留原始存檔，數值比對使用既定相對容差與對應絕對容差。
- [x] 本機 `python -m pytest -v` 為 13 通過、0 失敗、0 跳過。GitHub Ubuntu 的最新結果與 Python、Pillow 和 JPEG 函式庫版本由 M4 PR 的 Checks 查閱。CI 驗證存檔及在 runner 重新編解碼的數學與資料一致性。

## 待使用者或教師確認

- [ ] **正式題目與教師確認：待使用者確認。** 目前報告題目對應已完成的 JPEG／SVD 實驗。若教師要求維持浮水印題目，現有資料無法回答浮水印抗 JPEG 的問題。最小延伸可限定同一圖、固定嵌入設定及短位元序列，測未壓縮對照與 Q=80 的取回錯誤率，另量測嵌入失真。待使用者批准再實作，工時取決於是否有可靠的嵌入及取回方法。
- [ ] 填寫仍未知的學校／系級、教師及繳交日期。
- [x] M4 研究內容已完成外部審查，PR #5 已合併。
- [ ] 最終 PDF PR 待外部審查與使用者批准。

## 驗證範圍

本機重跑與 Ubuntu CI 是不同環境的執行證據。未要求兩個作業系統產生相同 JPEG 位元組，未測其他影像、編解碼器或浮水印。PDF 已包含圖表和公式，可獨立開啟。GitHub 保留原始數據及圖檔供重現。
