# 改良 blind_watermark 的 SVD 方法，降低 JPEG 壓縮後的浮水印 BER

> **唯一主要研究目標**：以 [guofei9987/blind_watermark](https://github.com/guofei9987/blind_watermark) 為基礎，改良其 **SVD 浮水印嵌入或擷取方法**，使浮水印經 JPEG 壓縮後，相對原版能以**更低位元錯誤率（BER）**正確擷取。未觀察到 BER 改善時，不得宣稱達成研究目標。

## 研究界線與成功條件

- **可修改**：上游 DWT→區塊 DCT→SVD 管線中的 **SVD 區塊嵌入及／或擷取演算法**；修改必須事前定義，且真正盲式擷取時不可使用原始浮水印位元或未受攻擊標記圖。
- **固定對照**：上游提交 `322c90dc02d45644692095b34d3a6b735b6edbd8`；其餘 DWT、DCT、洗牌、色彩、重複嵌入、聚合、K-means 與公開 bit API 原則上維持原版，JPEG 為黑盒攻擊。任何範圍變更須另外核准並揭露。
- **主要指標**：固定 JPEG Q10、4:4:4 的逐位 BER；Q20 為高壓診斷、Q30 為零錯誤對照。與原版同樣本、同位元、同金鑰、同編碼條件配對，並遵守事前固定的標記影像品質（例如 PSNR）判準。
- **次要指標**：PSNR、奇異值保序、矩陣範數、可計算性與可重現性只是品質限制、方法依據或輔助觀察，**不能取代 JPEG BER 改善**。
- **研究誠信**：保留全部失敗、負結果、原始輸出與版本；不以事後調參／選圖冒充獨立驗證，不以 96 個相依位元作獨立伯努利顯著性推論。

## 已完成的固定研究證據（尚未合併的工作保留在各 PR）

| 階段 | 研究內容 | JPEG Q10／4:4:4 錯誤數（每 96 位元） | 證據 |
|---|---|---:|---|
| W0／W0-D | 上游原版基準與壓力診斷 | **12／96** | [#13](https://github.com/Rookie-YCLin/matrix-jpeg-research/pull/13)、[#14](https://github.com/Rookie-YCLin/matrix-jpeg-research/pull/14) |
| G2 | 改第二奇異值量化步長 | d2=10：18／96；d2=30：19／96 | [#17](https://github.com/Rookie-YCLin/matrix-jpeg-research/pull/17) |
| G3 | 擷取端軟判決 | 13／96 | [#18](https://github.com/Rookie-YCLin/matrix-jpeg-research/pull/18) |
| G4 | 僅第一奇異值硬判決 | 17／96 | [#20](https://github.com/Rookie-YCLin/matrix-jpeg-research/pull/20) |
| G5 | 非負保序、最近格點嵌入 | 24／96 | [#21](https://github.com/Rookie-YCLin/matrix-jpeg-research/pull/21)、[#22](https://github.com/Rookie-YCLin/matrix-jpeg-research/pull/22) |

**現階段尚無在主要 Q10 條件下優於原版的候選方法。** G5 消除兩類嵌入奇異值排序違反事件，並改善 PNG PSNR，但 Q10 BER 變差；G5 同時改變量化準則及保序條件，其效果不能單獨歸因。不得將 G5 包裝成「抗 JPEG 改良成功」。

## 下一步（診斷優先，不啟動新候選）

先利用既有 W0-D 標記 PNG、JPEG 和公開擷取流程做唯讀 D0／D1／D2 診斷：聚合分數與 K-means 門檻、兩個奇異值通道的投票率、JPEG 前後餘數位移。必須先逐位重現公開 API；真值只用於離線評估，不能進入盲式解碼。沒有清楚、可證偽的機制及事前驗證計畫，不啟動新的 SVD 候選搜尋。

[正式規格](PROJECT_SPEC.md) · [固定證據索引](docs/EXPERIMENT_INDEX.md) · [工作規範](AGENTS.md) · [Codex 交接](docs/CODEX_NEXT_SESSION.md) · [研究進度](PROGRESS.md)

> 歷史 M0–M4、早期 SVD／JPEG 探索與已封存資料是研究沿革，不是目前能支持浮水印 BER 改善的正式證據；保留於 Git 歷史與既有路徑，不在首頁當作主線成果。
