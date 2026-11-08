# 盲式浮水印的 JPEG 抗壓縮與 SVD 區塊演算法改良

## 研究問題與範圍

以 `guofei9987/blind_watermark` 提交 `322c90dc02d45644692095b34d3a6b735b6edbd8` 為基礎，測試 JPEG 壓縮攻擊，只修改 SVD 區塊的擷取判決，檢驗是否能提升浮水印擷取強韌性。上游 DWT、分塊 DCT、係數洗牌、色彩轉換及重複嵌入皆沿用。JPEG 只作黑盒攻擊。[上游核心程式](https://github.com/guofei9987/blind_watermark/blob/322c90dc02d45644692095b34d3a6b735b6edbd8/blind_watermark/bwm_core.py) · [公開擷取介面](https://github.com/guofei9987/blind_watermark/blob/322c90dc02d45644692095b34d3a6b735b6edbd8/blind_watermark/blind_watermark.py) · [MIT 授權](https://github.com/guofei9987/blind_watermark/blob/322c90dc02d45644692095b34d3a6b735b6edbd8/LICENSE)

## 原版規則

原版 common 使用 4×4 區塊及 `fast_mode=False`。對位元 b，以 dⱼ(⌊sⱼ/dⱼ⌋ + 1/4 + b/2) 修改前兩個奇異值，d1=36、d2=20。擷取以 rⱼ=(sⱼ mod dⱼ)/dⱼ，當 rⱼ>1/2 判為 1。兩票按 3:1 融合，跨三通道及重複區塊取平均，再由公開 bit 介面執行一維 k-means 與位元順序還原。

## 已交付的實驗階段

- W0 是原版基準，W0-D 是固定含水印 PNG 上的 JPEG 壓力與分數診斷。G2 只探索 d2=10、20、30，在主要 Q10 條件未觀察到相近品質下的 BER 改善。各階段固定證據見[實驗索引](docs/EXPERIMENT_INDEX.md)。
- G3 是區塊演算法研究。在擷取端以 g(r)=(1−sin(2πr))/2 取代個別奇異值的硬判決，保留 3:1 權重、平均、分群和位元還原。兩個擷取器讀取同一批封存無攻擊 PNG 和 JPEG 解碼像素，保留原版嵌入與 d1=36、d2=20。原始位元僅作事後 BER 計算。
- G3 實測已交付，待人工研究驗收。主要 Q10 的原版及軟判決為 12/96、13/96，未達改善目標。Q20 的局部變化及 Q30 對照應按預定用途分開解讀。結論限於三圖、單一 payload 與固定編碼條件。[G3 PR #18](https://github.com/Rookie-YCLin/matrix-jpeg-research/pull/18)

保留 [舊全影像研究規格](https://github.com/Rookie-YCLin/matrix-jpeg-research/blob/ede4ce330b2e21790cacf3bb6fed879e8b79ec67/PROJECT_SPEC.md)、歷史程式與實驗資料。
