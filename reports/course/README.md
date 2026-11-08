# 課程專題編製筆記

以 main 的 86cf6e2 為起點。正文以 G6_FINAL_PROJECT_REPORT.md 和 SVD_QIM_MATRIX_THEORY.md 為依據。

圖表重跑需使用固定 Python 3.13 與 PSNR 報告的依賴。先在新目錄執行 python -m experiments.svd_qim_psnr --output-dir <paired>，再執行 python reports/course/build_figures.py --paired <paired> --output <new-figures>。生成器先核對配對 PSNR 的六個封存雜湊，再畫圖。QF 比較圖重編碼原版含水印 PNG，設定 Pillow RGB、4:4:4、optimize=False、progressive=False。QF5、15、50 的重生檔與 BER 封存相同，QF95 不同，須標為重生示例。BER 與 PSNR 圖直接讀已合併 CSV；QIM 與流程圖為示意。

正文取用中山大學格式規範第十四至十六點的 A4、上／下 2.54 cm、左／右 3 cm、中文 12 pt 標楷體、1.5 倍行距、英文 12 pt Times New Roman、頁碼及圖源格式。課程報告省略學位論文審定、授權與書脊。周孜燦老師講義可參考其「具體例子、變數命名、一般規則、圖示驗證」的順序。正文從血小板裁切提出問題，再解釋指標、區塊流程、QIM 格點、擾動界及畫質取捨。

## Word 與 PDF 編製

建議使用支援 python-docx 1.2、lxml 與 latex2mathml 3.81.1 的 Python 環境。先生成圖表，再執行：

    python reports/course/build_report.py --figures <figures> --output <report.docx> --math-xsl <Office MML2OMML.XSL>

公式以可編輯的 Word 公式物件寫入。以 Word 開啟、重新分頁並匯出 PDF，再以 pdfinfo、pdffonts 及 pdftoppm 核對紙張、字型及每頁。PDF 與 DOCX 皆由同一來源生成。此次 Word 匯出為 18 頁，包含封面、摘要、15 頁正文及參考資料；標楷體、Times New Roman 和公式用 Cambria Math 均嵌入。此次環境未安裝 LibreOffice，視覺查核採 Word 的實際排版結果。
