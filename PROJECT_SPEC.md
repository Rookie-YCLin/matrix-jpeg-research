# SVD 奇異值嵌入參數對盲浮水印 JPEG 攻擊後 BER 的影響

## 研究問題與範圍

在相近的含浮水印影像品質下，調整奇異值嵌入參數或一項簡單嵌入改良，能否降低 JPEG 攻擊後的盲浮水印 BER？主要研究對象固定為 `guofei9987/blind_watermark` 提交 `322c90dc02d45644692095b34d3a6b735b6edbd8` 的 [bwm_core.py](https://github.com/guofei9987/blind_watermark/blob/322c90dc02d45644692095b34d3a6b735b6edbd8/blind_watermark/bwm_core.py)。另核對 [公開 bit 介面](https://github.com/guofei9987/blind_watermark/blob/322c90dc02d45644692095b34d3a6b735b6edbd8/blind_watermark/blind_watermark.py) 和 [MIT 授權](https://github.com/guofei9987/blind_watermark/blob/322c90dc02d45644692095b34d3a6b735b6edbd8/LICENSE)。上游既有 DWT、分塊 DCT、係數洗牌、色彩轉換與重複嵌入照原程式保留。JPEG 僅作黑盒編解碼攻擊，不分析其 DCT、量化表或頻譜。

## 上游規則與待驗證假說

使用 `fast_mode=False`、4×4 區塊及原版 common 路徑。令 b 為該塊嵌入位元，兩個奇異值各以步長 dⱼ 映射為 dⱼ(⌊sⱼ/dⱼ⌋ + 1/4 + b/2)，原版 d1=36、d2=20。提取時以 sⱼ mod dⱼ > dⱼ/2 判位，兩票按 3:1 融合。跨三通道及重複區塊平均後，公開 `mode="bit"` 走上游一維 k-means，再依原規則還原位元順序。這些是程式行為。改變 d2 是否降低 BER、是否仍有相近 PSNR，都須由配對實測判定。

## 第一階段 W0／G1

依 [Issue #10](https://github.com/Rookie-YCLin/matrix-jpeg-research/issues/10) 凍結固定 RGB 影像、32-bit payload、密鑰、原版參數及編解碼設定。先驗證無攻擊 PNG，再從同一含浮水印 PNG 獨立編碼 JPEG Q40、60、80、95。報告逐影像、逐條件的錯誤位元數、總位元數、BER 與 PSNR，保存逐位結果、設定、版本、來源、雜湊和重跑證據。主要 BER 統一採用原版 bit 擷取。固定閾值可另列診斷結果。

## 第二階段 G2

W0／G1 無攻擊基準成功、可重現並通過研究審查後，另開議題和 PR，只比較 d2=10、20、30，d1 固定 36，嵌入端與擷取端同步設定。固定影像、payload、密鑰、格式、編解碼器與擷取策略。逐影像及 Q 比較 BER 與含浮水印影像 PSNR 的權衡，事前定義「相近 PSNR」的判準再看 G2 結果。若沒有可比的影像品質或 BER 未降，如實呈現。其他嵌入改良須另立比較，有限樣本不支撐普遍改善主張。

## 歷史基線

[原版規格](https://github.com/Rookie-YCLin/matrix-jpeg-research/blob/ede4ce330b2e21790cacf3bb6fed879e8b79ec67/PROJECT_SPEC.md)、既有程式、13 項測試、M2 輸出與報告保留供重現。[PR #7](https://github.com/Rookie-YCLin/matrix-jpeg-research/pull/7) 與 [PR #12](https://github.com/Rookie-YCLin/matrix-jpeg-research/pull/12) 分別保存 PDF 與 R1 的程式、測試和資料。R1 已交付待審，R2 暫緩。
