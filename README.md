# 以改良 SVD 浮水印演算法提升 JPEG 抗壓縮能力

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
