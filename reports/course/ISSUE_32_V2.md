# G6 課程報告 V2.0 修訂紀錄

依據 [Issue #32](https://github.com/Rookie-YCLin/matrix-jpeg-research/issues/32) 修訂。實驗資料以 `86cf6e2e2a07c75ec179ad3448818ae3c4586fc8` 為準。

| 項目 | 修訂與驗收 |
| --- | --- |
| H1 貢獻 | 第一章分開上游初始化註解、Bernstein 矩陣結果、本文局部條件推導及受控實測。保留原版架構與 QIM 推導。 |
| H2 全位反相 | 第五章列出真值分組範圍、中心與閾值。另附兩組各 32 個分群前分數、還原順序、雜湊與原始輸出。QF15 原版高分為真值 0，分群前已呈反向。真值只供事後分析。 |
| H3 選擇 90 | 第五章直接讀取探索 CSV，列四組步長及四個 QF 的錯誤數。60、72 在 QF15 皆為 0/32，在 QF10 分別為 32/32 與 29/32。90 為有限候選的工程選擇。 |
| H4 來源 | Word 外部連結與 PDF URI 指向上游、patch、CSV、manifest、診斷、重現及 CI。Bernstein 採原書印刷頁碼。課堂講義為本機附件，未取得公開網址。 |
| H5 插畫 | 首次出現標為上游提供的血小板角色插畫。公開再製權未確認。含圖版提供課堂審閱，GitHub 保存生成程式及圖源雜湊。 |
| M1 證據層次 | 第一章新增對照表。 |
| M2 圖表 | 保留七圖。更新 QIM 週期與裕度、BER 兩個重點、兩個 PSNR 差值及色彩轉換與金鑰流程。 |
| M3 排版 | 封面改在完整詞組前換行。PSNR 引表段落與表格同頁。 |
| M4 文字 | 六個關鍵詞。圖表與實驗來源以編號追溯。 |
| M5 可攜性 | Word 公式為原生 OMML，正式版 PDF 嵌入公式字型。其他 Word 引擎未驗證。 |
| M6 重現 | 指令採等寬字型，另附 QF15 診斷重現命令。 |
| M7 QF95 | 標示重生檔與封存位元組不同，原因未確認。 |
| M8 定位 | 課程專題範圍保留固定來源與受控條件。 |
| M9 示意 | 保留教學用二階矩陣與 +12 量化門檻跨越例。 |

## 診斷重現

沿用配對 PSNR manifest 的環境與輸出目錄。診斷程式比對正式 BER 封存的 QF15 檔案 SHA-256，以追蹤方式記錄公開解碼呼叫中的分群前分數與最終中心。用同一金鑰順序對照分數及真值。

```text
python -m experiments.svd_qim_psnr --output-dir <paired>
python -m reports.course.diagnose_qf15 --paired <paired> --output <new-json>
python reports/course/build_figures.py --paired <paired> --output <new-figures>
```

完整生成圖雜湊見 [figure-provenance-v2.json](figure-provenance-v2.json)。V1 分支與原始數據保留。
