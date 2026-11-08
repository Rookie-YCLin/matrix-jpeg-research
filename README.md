> **2026-11-08 正式收尾：** G6 單參數 d1=36→90 的 BER、PSNR 與矩陣理論已全部完成；[正式整合報告](reports/G6_FINAL_PROJECT_REPORT.md) · [教授角度審查](reports/G6_FINAL_REVIEW_CHECKLIST.md) · [完整推導](reports/SVD_QIM_MATRIX_THEORY.md) · [PSNR 實測](reports/SVD_QIM_PSNR_TRADEOFF.md)。主條件 JPEG QF15：BER 32/32→0/32，PSNR 29.225→27.554 dB（−1.671 dB）；QF5 仍有已知退步。已合併 [PSNR PR #29](https://github.com/Rookie-YCLin/matrix-jpeg-research/pull/29) 和 [理論 PR #30](https://github.com/Rookie-YCLin/matrix-jpeg-research/pull/30)。**以下歷史階段文字若提到「待補 PSNR」「尚未完成 G6」「仍需候選搜尋」，均不是目前狀態。**

> **2026-11-08 最新研究交接：** G6 單參數 d1=36→90 已完成且封存 BER 實測；後續 **只補 PSNR（QF15 影像品質 trade-off）與有脈絡的矩陣理論推導**。固定 d2=20、同一張圖片與 32-bit payload；不搜尋新步長、不研究 QF<15 機制、不追求全域最優。詳見 [最新工作規格](docs/RESEARCH_NEXT_PHASE.md)、[Codex PSNR 提示詞](docs/PROMPT_CODEX_PSNR.md)、[Work 理論提示詞](docs/PROMPT_WORK_MATRIX_THEORY.md)。**較下方「不需要 PSNR」敘述為舊階段規格，已由本段取代。**

# 改良 blind_watermark SVD 以提升低 QF JPEG 浮水印強韌性

## 專題已達標：G6 SVD 量化改良（2026-11-08）

- 將上游 `bwm_core.py` 的第一奇異值 QIM 步長 **d1: 36 → 90**，第二奇異值 d2=20、其他浮水印管線皆維持原版；屬 SVD 區塊內的改良。
- 使用者事前固定的最壞原版 QF **x=15**：原版 **32/32 錯（BER 100%）**，G6 **0/32 錯（BER 0%）**，**相對 BER 降幅 100%**，超過 10% 優秀標準。
- 完整 QF 掃描：QF10、15、20 改善；QF25～95 兩者均0錯；**QF5 由 12/32 變成 32/32，並非全低 QF 改善**。另用兩組未參與選參數的32-bit序列驗證 QF15 均0錯。
- [成功方法、理論及限制](reports/G6_SVD_QIM_QF15_SUCCESS.md) · [實測 CSV](outputs/svd-qim-qf15-selected/results.csv) · [最小上游 patch](patches/bwm_core_svd_d1_90.patch) · [驗證 CI](https://github.com/Rookie-YCLin/matrix-jpeg-research/actions/runs/42463429539)。按已核准的研究規格，**已取得正向結果，停止新增候選搜尋**。


## 最新原版實測｜唯一指定原圖（W1）

[W1 實測與重現](outputs/ori-qf-scan/README.md) · [19 個 QF 的 BER CSV](outputs/ori-qf-scan/results.csv) · [GitHub Actions](https://github.com/Rookie-YCLin/matrix-jpeg-research/actions/runs/42461739759)

- 指定 `ori_img.jpeg` 的原版 QF=15、20 均為 **32/32 錯誤（BER 100%）**，依並列取最小 QF 的事前規則，**正式選擇 x=15**。QF=5 為 12/32，QF=10 為 1/32，QF=25–95 均為 0/32。無攻擊 PNG 為 0/32。
- **待改良的正式門檻**：在固定 QF=15 時，候選至多 **30/32** 錯誤達相對改善 ≥5%，至多 **28/32** 錯誤達 ≥10%。目前僅原版基準，尚未測試改良。
- QF15、20 原版擷取的全部位元與真實 payload 互補，值得進一步分析整體極性反轉；不可只按已知真值反相就宣稱完成盲式演算法改良。


**倉庫管理授權（2026-11-08）**：研究主持人已授權專題倉庫全權管理；代理可自行建立、修訂、刪除適當檔案、開啟與合併 PR、更新 `main`、執行既定實驗及管理分支，**不需要逐項徵求批准**。保留可重現證據、上游授權及真實研究紀錄；重大研究判斷自主決策並在互動中主動回報。

**主持人已核定（2026-11-08）**：完整掃描 **QF=5、10、15、…、95（19 點）**；原版 BER 最大值若有多個 QF 並列，**取其中最小 QF**，將該值固定為 `x`，再測試 SVD 候選。相對 BER 降幅 `R=(BER_base(x)-BER_new(x))/BER_base(x)×100%`，**R≥5% 達標，R≥10% 優秀**。這些已非待決設定。


## 最新固定測試規格：一張指定原圖、最大原版 BER 的 QF（2026-11-08）

- **唯一測試來源**：[上游指定測試圖](https://github.com/guofei9987/blind_watermark/blob/master/examples/pic/ori_img.jpeg)（`examples/pic/ori_img.jpeg`；已核對 Git blob SHA `ef48a056b3cab1d2c08723c014d8d515963f5a07`）。先封存原始檔及 SHA-256，再依原版實際嵌入流程產生帶浮水印影像。
- **QF 掃描**：先對原版測試 QF 為 5 倍數的 JPEG 壓縮條件；已核准 `5,10,…,95`，此範圍已固定。以實測 BER 最高的 QF 為 `x`；最高 BER 如有多個並列，須先固定同分選取規則，不得事後挑最有利的一個。
- **主要驗收（已核准）**：在固定 `QF=x`、同一原圖、同一 payload、同密鑰與編碼條件下，**相對 BER 降幅 ≥5% 達標，≥10% 為優秀**。定義 `R=(BER_base(x)-BER_new(x))/BER_base(x)×100%`，亦可直接以相同總位元數下的錯誤數計算。必須報告原版／改良版錯誤數、分母、BER 與相對降幅；不可將 5% 解讀為 5 個百分點。若 `BER_base(x)=0`，相對降幅不成立，須先重新檢查基準與成功判準。
- **規避偏差**：`x` 由原版結果確定後凍結，不能因候選結果而更換；反覆試候選可作本專題內部探索，但最終結論僅限此圖及指定測試條件，勿宣稱其他圖片普遍改善。
- **歷史數據定位**：先前 W0–G5 的三張 skimage 圖與 QF10/20/30 結果是**歷史探索**，不能套用為新指定原圖的原版基準。需先完成新圖的原版 QF–BER 掃描才可決定 `x`。


> **正式研究目標**：以 [guofei9987/blind_watermark](https://github.com/guofei9987/blind_watermark) 為 Source Code，修改其 **SVD 浮水印嵌入或擷取方法**，改善低 JPEG Quality Factor（QF，強壓縮）下的浮水印位元錯誤率（BER）。

## 專題三步驟

1. **原版基準**：先重現上游 [bwm_core.py](https://github.com/guofei9987/blind_watermark/blob/master/blind_watermark/bwm_core.py) 的浮水印嵌入與擷取。上游 [att.py](https://github.com/guofei9987/blind_watermark/blob/master/blind_watermark/att.py) 未提供本專題要求的 JPEG 壓縮攻擊測試，因此另寫獨立的 JPEG 編碼／解碼測試，量測**不同 JPEG QF 的 BER**。固定上游提交 `322c90dc02d45644692095b34d3a6b735b6edbd8`，避免 master 後續變動影響重現。
2. **改良 SVD**：針對低 QF 的 BER，在 `bwm_core.py` 對應的 SVD 區塊中自行設計嵌入及／或擷取方法。保留非研究變因，以與原版進行同條件、同金鑰、同 payload、同 JPEG QF 的比較。
3. **持續迭代，取得正向結果即停止候選搜尋**：對候選先固定方法與測試條件，再執行與原版的 BER 比較。只要在預先指定的低 QF 條件下取得可重現的 BER 下降，且能用矩陣理論合理解釋，就可定為專題最終方法；不能僅憑一次偶然降低宣稱通用強韌性。

## 成果口徑與檔案管理

- **唯一正式性能指標為 BER 隨 JPEG QF 的變化**。不要求額外加入 PSNR 等品質指標。
- **對外交付的專題報告**：著重原版、成功改良、矩陣理論與 BER–QF 結果。無須逐一敘述失敗候選；但不能虛構改善、挑選或隱瞞會改變主要結論的測試，也不得對已知相反結果作誤導宣稱。
- **GitHub 內部研究紀錄**：完整保留嘗試、負結果、參數、測試、CSV、程式版本、PR、失敗日誌，以利審查及重現；研究報告簡潔與研究紀錄完整是不同層次。
- 每階段經由本倉庫新增、修改、整理文件與程式，採獨立分支與 PR 管理，經自我驗證後可直接合併 `main`，不需人工批准；清理冗餘檔案時保留必要研究證據。
- 進度回報格式：**目前階段／本次完成／最新各 QF BER／阻礙與風險／下一步與待決事項**。重大不確定的研究選擇由倉庫管理者合理裁決並回報；不得擅自誇大或虛構成功。
  
## 現有研究的定位

原版與早期候選的測試數據仍保存在 [實驗索引](docs/EXPERIMENT_INDEX.md) 及既有 PR。這些是**內部探索與基準紀錄**，不等於已完成目標。下一步可先利用既有資料診斷低 QF BER 的錯誤機制，再提出下一個有理論依據的 SVD 候選。

[完整規格](PROJECT_SPEC.md) · [代理規範](AGENTS.md) · [實驗索引](docs/EXPERIMENT_INDEX.md) · [Codex 交接](docs/CODEX_NEXT_SESSION.md) · [研究進度](PROGRESS.md)
