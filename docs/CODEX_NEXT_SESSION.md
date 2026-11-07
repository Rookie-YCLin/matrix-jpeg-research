# Codex 下一次工作階段交接卡｜先讀，切勿跳步

> **G0 已核准 A（2026-11-08，最新研究者指示）**：本週改以 SVD 盲浮水印抗 JPEG 最小研究為主線；PR #7 為交件備案。**下一步唯一工作包是 [Issue #10 W0/G1](https://github.com/Rookie-YCLin/matrix-jpeg-research/issues/10)；不可跳到 G2。** 本文件位於 Draft PR #9 分支，尚未併入 `main`。

## 最先讀這段：分支與授權防呆

**目前此交接卡、更新的 AGENTS.md 與 README.md 只存在於 Draft PR #9 分支** `planning/watermark-7day-charter`，不是預設的 `main`！Codex 不可只讀 `main/AGENTS.md` 就宣稱已接收新版規則。

```sh
git fetch origin
git switch planning/watermark-7day-charter
git pull --ff-only
git status --short
```

上述僅作**讀取 PR #9 研究規劃**，不要在此分支寫入浮水印實驗。若環境沒有本地分支，使用 `git switch -c planning/watermark-7day-charter --track origin/planning/watermark-7day-charter`。若工作樹未清空、分支已有他人更新或 checkout 失敗，**不可用 `reset --hard`、`clean -fd` 或 force push 解決**；先回報。閱讀完成後，開工前回到使用者已授權的目標分支，；本次 G0=A 已授權 Issue #10 的 G1 baseline。

**首次回報只要四行：** ① 目前所在分支／HEAD SHA；② G0 已核准 A 而 G1 尚未驗收；③ PR #7、#9、Issue #8/#10 的角色；④ 如何建立 W0/G1 獨立分支、實際進行 baseline 與停損。**G1 已獲授權，可在獨立新分支開工；PR #9 僅供讀取規範，不得直接在規劃分支寫實驗。**

## 研究室去蕪存菁守則｜Codex 必讀

**唯一優先順序：** G0 **已核准 A** → **現在做 W0/G1 上游 baseline** → G1 外部審查 → G2 單因子比較 → G3 正式報告。禁止因「可以做」就自行增加新實驗。

**現有資料分級（不刪除）**
- **已驗證基準**：`main` 的 `PROJECT_SPEC.md`、程式、`data/ascent.png`、`outputs/run-m2`、測試與 M3；不得覆蓋。
- **繳交備案**：PR #7 的 11 頁 PDF 與來源，仍 open，尚缺封面資料；不與浮水印研究混寫。
- **已核准主線**：G0=A 已經由研究者決定；Issue #8 管研究方向、Issue #10 管當前 G1 baseline、Draft PR #9 管交接文件；G1 尚未驗收，不得假裝已有結果。
- **歷史探索**：已遺失原始碼/CSV 的舊浮水印報告；可當假說來源，不能當結果引用。
- **後續想法**：DFT、全圖秩一方向、量化代理、ECC 等先記在既有 Issue，不另開平行工作或堆一批新檔。

**最小化倉庫原則**：新成果只留下「能重現／支撐論證」的程式、設定、必要 CSV、測試和精選圖。暫存圖、重複 PDF、實驗中間檔不得無限制提交。清理舊檔前先在 PR 列出「保留／歸檔／候選刪除」清單與理由，**未獲研究者批准，不刪改已驗收成果**。

**每次 Codex 執行的任務格式**（只做一件）：
1. **目的**：這次唯一要回答的問題；一段話說清楚。
2. **允許範圍**：可修改哪些檔案、固定哪些設定、明確禁止什麼。
3. **驗收條件**：可檢查的數據／測試／文件／圖形，不接受「看起來完成」。
4. **交付證據**：commit SHA、PR、命令、CSV、失敗與未完成事項。
5. **停損條件**：資料不足、baseline 失敗、結果不一致、超出範圍時，先回報，不要擅自發明新方法或補數據。

**自我檢查**：在 PR 描述的最上方用 3 句話回答「我為何做？我改了什麼？證據在哪裡？」。如果無法回答，先不要送審。ChatGPT 將對照原始碼、原始數據與輸出獨立驗收；CI 成功不是研究成功。

## 目前 GitHub 真實狀態

- 專案：`Rookie-YCLin/matrix-jpeg-research`，私有；`main` 是既有全影像 JPEG／SVD 已驗證成果。
- [PR #7](https://github.com/Rookie-YCLin/matrix-jpeg-research/pull/7) 原有 11 頁單欄 PDF 已外部審查為 **PASS WITH CONDITIONS**，但封面未填；仍 open，**不得合併、關閉、重寫或把它當作浮水印成果**。
- [Issue #8](https://github.com/Rookie-YCLin/matrix-jpeg-research/issues/8) 是使用者真正感興趣的 blind_watermark SVD 嵌入抗 JPEG 議題。
- 先讀 `docs/ONE_WEEK_RESEARCH_CHARTER.md`；它的研究範圍 **G0 已核准**，但不是已經測得的實驗結果。既有 `PROJECT_SPEC.md` 目前明確排除浮水印實驗。
- 歷史三篇浮水印報告的原始碼／CSV 已被刪除，舊 BER 數字**不可直接視為真實可重現的成績**。

## 下一次僅有一個先決問題

**研究者已選 A，已完成 G0；[Issue #10](https://github.com/Rookie-YCLin/matrix-jpeg-research/issues/10) 是本次唯一可開始的工作包。** 請從 `main` 另開 `research/w0-watermark-baseline` 等新分支，只完成 G1 原版基準，不直接做最佳化或長篇 PDF：

1. 鎖定 `guofei9987/blind_watermark` 上游 commit 與授權；核對 `bwm_core.py` 的 SVD `d1,d2` 嵌入、盲擷取路徑與預設參數。
2. 固定 3 張合法影像、32-bit 位元、seed、common mode、`d1=36,d2=20`、Pillow JPEG Q=40/60/80/95；從同一無損含水印圖獨立攻擊。
3. 先證明 PNG 無攻擊時嵌入／盲擷取成功，再記錄 JPEG 後逐影像 BER、PSNR、錯誤位元數與 manifest。
4. 程式需有最基本的可重現測試，不能污染原 M2 輸出；產出原始 CSV、環境、命令、失敗案例。
5. **G1 通過、原始 CSV 與提取正確性完成獨立審查，才提出 `d2=10,20,30` 的 G2 實驗；不得提前宣稱改良成功。**
6. 本工作包的完整可編輯規格與驗收門檻以 [Issue #10](https://github.com/Rookie-YCLin/matrix-jpeg-research/issues/10) 為準；請勿單靠本交接卡省略細節。

## 工作規範

- 每個工作包只問一個研究問題，保留原始碼、失敗與設定；可用 GitHub PR 對話向研究者／ChatGPT 申請審查。
- 優先研究**位元 BER 與 PSNR 的公平權衡**，不偷換為 JPEG 檔案壓縮率、SVD rank-k 自身誤差或任何非盲式解碼成績。
- 不隨意自行擴張到 DFT、全影像秩一基底、量化預測、多種 ECC、深度學習、GUI、超大資料集。
- 圖文讀者導向、公式要有動機；數學正確比文案漂亮重要；不要以 pytest 通過當成演算法性能證明。
- 向使用者回報：最新 SHA、PR/Issue、所作／未作、實際測試、原始數據位置、風險、下一步。