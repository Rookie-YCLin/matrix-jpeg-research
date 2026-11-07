# Codex 下一次工作階段交接卡｜先讀，切勿跳步

> 狀態：**待研究者確認新研究方向**。本文件隨「一週研究範圍」規劃 PR 出現，並不自行改寫 `PROJECT_SPEC.md`。

## 目前 GitHub 真實狀態

- 專案：`Rookie-YCLin/matrix-jpeg-research`，私有；`main` 是既有全影像 JPEG／SVD 已驗證成果。
- [PR #7](https://github.com/Rookie-YCLin/matrix-jpeg-research/pull/7) 原有 11 頁單欄 PDF 已外部審查為 **PASS WITH CONDITIONS**，但封面未填；仍 open，**不得合併、關閉、重寫或把它當作浮水印成果**。
- [Issue #8](https://github.com/Rookie-YCLin/matrix-jpeg-research/issues/8) 是使用者真正感興趣的 blind_watermark SVD 嵌入抗 JPEG 議題。
- 先讀 `docs/ONE_WEEK_RESEARCH_CHARTER.md`；它是**提案**，不是已經測得的結果。既有 `PROJECT_SPEC.md` 目前明確排除浮水印實驗。
- 歷史三篇浮水印報告的原始碼／CSV 已被刪除，舊 BER 數字**不可直接視為真實可重現的成績**。

## 下一次僅有一個先決問題

**使用者是否正式同意把一週課程研究目標切換到新浮水印題目？**

若未確認：只說明範圍、影響、所需工時；不可擅自啟動大型實驗／重寫報告或移動 PR #7。

若已確認，**只開 W0 baseline 的獨立 issue／branch，先做 G1，不直接做最佳化或長篇 PDF**：

1. 鎖定 `guofei9987/blind_watermark` 上游 commit 與授權；核對 `bwm_core.py` 的 SVD `d1,d2` 嵌入、盲擷取路徑與預設參數。
2. 固定 3 張合法影像、32-bit 位元、seed、common mode、`d1=36,d2=20`、Pillow JPEG Q=40/60/80/95；從同一無損含水印圖獨立攻擊。
3. 先證明 PNG 無攻擊時嵌入／盲擷取成功，再記錄 JPEG 後逐影像 BER、PSNR、錯誤位元數與 manifest。
4. 程式需有最基本的可重現測試，不能污染原 M2 輸出；產出原始 CSV、環境、命令、失敗案例。
5. **G1 通過才提出 `d2=10,20,30` 的 G2 實驗；不得提前宣稱改良成功。**

## 工作規範

- 每個工作包只問一個研究問題，保留原始碼、失敗與設定；可用 GitHub PR 對話向研究者／ChatGPT 申請審查。
- 優先研究**位元 BER 與 PSNR 的公平權衡**，不偷換為 JPEG 檔案壓縮率、SVD rank-k 自身誤差或任何非盲式解碼成績。
- 不隨意自行擴張到 DFT、全影像秩一基底、量化預測、多種 ECC、深度學習、GUI、超大資料集。
- 圖文讀者導向、公式要有動機；數學正確比文案漂亮重要；不要以 pytest 通過當成演算法性能證明。
- 向使用者回報：最新 SHA、PR/Issue、所作／未作、實際測試、原始數據位置、風險、下一步。