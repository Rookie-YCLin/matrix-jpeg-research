# 正式研究規格｜SVD 浮水印改良與 JPEG 抗壓縮能力

## 1. 不可偏離的主要目標

> **以 [guofei9987/blind_watermark](https://github.com/guofei9987/blind_watermark) 為基礎，改良其 SVD 浮水印嵌入或擷取方法，使浮水印經 JPEG 壓縮後，以比原版更低的位元錯誤率（BER）被正確擷取。**

主要研究指標是 **JPEG 後的 BER**。影像品質（PSNR）、SVD 保序、Frobenius 失真、數學證明及程式可重現性均為必要的約束、分析或次要結果，**不得替代 BER 的成效判準**。若無有效改善，研究結論須明確寫「主要目標未達成」。

## 2. 基準及允許改動

- **上游與版本**：`guofei9987/blind_watermark`，固定提交 `322c90dc02d45644692095b34d3a6b735b6edbd8`。[bwm_core.py](https://github.com/guofei9987/blind_watermark/blob/322c90dc02d45644692095b34d3a6b735b6edbd8/blind_watermark/bwm_core.py) · [公開 bit 介面](https://github.com/guofei9987/blind_watermark/blob/322c90dc02d45644692095b34d3a6b735b6edbd8/blind_watermark/blind_watermark.py) · [MIT 授權](https://github.com/guofei9987/blind_watermark/blob/322c90dc02d45644692095b34d3a6b735b6edbd8/LICENSE)。
- **允許研究的變因**：**SVD 區塊的嵌入方法、擷取方法或兩者**。原版 DWT、區塊 DCT、區塊洗牌、色彩轉換、跨區塊與通道聚合、公開 API、一維 K-means 與金鑰還原固定為控制條件，除非主持人明確批准擴大範圍。
- **盲式要求**：最終擷取只能取得受攻擊圖、必要金鑰、預先設定參數及尺寸；不能使用正確 payload、未受攻擊標記圖或原圖作判決。這些資料僅供事後評估與機制診斷。
- **上游原版規則**：common、`fast_mode=False`、4×4 SVD 區塊。原版嵌入 `q_j=d_j(floor(s_j/d_j)+1/4+b/2)`，(d_0=36,d_1=20)；擷取由奇異值餘數硬判決、3:1 融合、跨區塊平均、`one_dim_kmeans` 與位元順序還原完成。須區分「修改嵌入」與「修改擷取」，不得把 G5 當作只改擷取。

## 3. 比較與驗證規則

- **主要條件**：三張固定 RGB 圖、固定 32-bit payload、金鑰與 codec、JPEG Q10／4:4:4；原版基準 **12／96（BER 12.50%）**。Q20／4:4:4 為高壓失效分析（原版 78／96）；Q30 為零錯誤對照（原版 0／96）；無攻擊 PNG 也須保留。
- 任何新方法要**事前登錄**公式、改動面、必要參數、樣本、固定品質限制與成功條件，然後在完全相同條件下配對。嵌入端修改時，需從各自的標記 PNG 獨立生成 JPEG；僅改擷取端時兩版共用同一批 JPEG。
- **成功標準**：在事前固定的品質限制內，主要 Q10 BER **低於**原版，且不存在隱藏的取樣或基準變更。這表示觀察改善；若要宣稱具有一般化抗壓能力，還需要未參與方法選擇的獨立影像／payload 驗證。
- 所有負結果須逐圖揭露。不可把單一 Q20 局部改善、PNG PSNR、排序修正、Q30 零錯誤或統計假說改寫成主要目標達成；不可把相依的 96 個位元當獨立實驗樣本做顯著性檢定。

## 4. 固定研究歷史與暫停線

- **W0、W0-D**：基準與 JPEG 壓力診斷，[#13](https://github.com/Rookie-YCLin/matrix-jpeg-research/pull/13)、[#14](https://github.com/Rookie-YCLin/matrix-jpeg-research/pull/14)。Q10 12／96，Q20 78／96，Q30 0／96。
- **G2**：第二奇異值步長探索，[#17](https://github.com/Rookie-YCLin/matrix-jpeg-research/pull/17)；未改善主要 Q10。
- **G3**：擷取端軟判決，[#18](https://github.com/Rookie-YCLin/matrix-jpeg-research/pull/18)；Q10 13／96。
- **G4**：第一奇異值硬判決，[#20](https://github.com/Rookie-YCLin/matrix-jpeg-research/pull/20)；Q10 17／96。
- **G5**：前置排序與相位診斷 [#21](https://github.com/Rookie-YCLin/matrix-jpeg-research/pull/21)；非負保序最近格點嵌入 [#22](https://github.com/Rookie-YCLin/matrix-jpeg-research/pull/22)，Q10 24／96，PNG PSNR 改善但**未通過事先固定的 ±0.5／±1.0 dB 品質匹配窗口**，不得宣稱品質匹配下的抗壓結論。
- **G2–G5 候選搜尋已結束**。下一步只允許先利用現有檔案做唯讀的 D0（分數與門檻）、D1（通道投票）、D2（JPEG 餘數位移）失效機制分析。任何進一步候選、新 payload、參數搜尋、合併或正式實驗均須另行核准，不能因為目標未達成就無限擴張。

## 5. 歷史留存與專案整理

- 已產生的原始結果、CSV、manifest、雜湊、測試、上游授權、歷史 PR 與負結果是可重現證據；**禁止為使首頁看來成功而刪除**。
- 歷史低秩重建與一般 JPEG 頻譜分析（M0–M4 等）只屬於探索背景，不應放在現行研究首頁或冒充浮水印 BER 證據。整理時優先刪減重複敘事及失效指示；移除資料或程式須先確認依賴並保留可追溯連結。
- 任何對 `main` 的合併都需要研究主持人明確批准。
