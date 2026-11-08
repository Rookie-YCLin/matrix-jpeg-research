# 改良 blind_watermark SVD 以提升低 QF JPEG 浮水印強韌性

**主持人已核定（2026-11-08）**：完整掃描 **QF=5、10、15、…、95（19 點）**；原版 BER 最大值若有多個 QF 並列，**取其中最小 QF**，將該值固定為 `x`，再測試 SVD 候選。相對 BER 降幅 `R=(BER_base(x)-BER_new(x))/BER_base(x)×100%`，**R≥5% 達標，R≥10% 優秀**。這些已非待決設定。


## 最新固定測試規格：一張指定原圖、最大原版 BER 的 QF（2026-11-08）

- **唯一測試來源**：[上游指定測試圖](https://github.com/guofei9987/blind_watermark/blob/master/examples/pic/ori_img.jpeg)（`examples/pic/ori_img.jpeg`；已核對 Git blob SHA `ef48a056b3cab1d2c08723c014d8d515963f5a07`）。先封存原始檔及 SHA-256，再依原版實際嵌入流程產生帶浮水印影像。
- **QF 掃描**：先對原版測試 QF 為 5 倍數的 JPEG 壓縮條件；已核准 `5,10,…,95`，此範圍須在測試前固定並由主持人核准。以實測 BER 最高的 QF 為 `x`；最高 BER 如有多個並列，須先固定同分選取規則，不得事後挑最有利的一個。
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
- 每階段經由本倉庫新增、修改、整理文件與程式，採**獨立分支 + Draft PR + 人工審查**。不擅自刪除可重現證據或合併 `main`。
- 進度回報格式：**目前階段／本次完成／最新各 QF BER／阻礙與風險／下一步與待決事項**。重大不確定的研究選擇要詢問主持人；不得自行更改範圍或宣稱成功。
  
## 現有研究的定位

原版與早期候選的測試數據仍保存在 [實驗索引](docs/EXPERIMENT_INDEX.md) 及既有 PR。這些是**內部探索與基準紀錄**，不等於已完成目標。下一步可先利用既有資料診斷低 QF BER 的錯誤機制，再提出下一個有理論依據的 SVD 候選。

[完整規格](PROJECT_SPEC.md) · [代理規範](AGENTS.md) · [實驗索引](docs/EXPERIMENT_INDEX.md) · [Codex 交接](docs/CODEX_NEXT_SESSION.md) · [研究進度](PROGRESS.md)
