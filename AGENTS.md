# AGENTS.md｜研究室常駐規則（Codex 必讀）

本倉庫是**矩陣理論／影像處理研究室**，不是任意生成 PDF 或嘗試演算法的練習場。研究者決定題目與結論；Codex 實作可重現實驗；ChatGPT 進行獨立數學／數據／論述審查。

## 開始前，先確認是哪一條研究線
1. **正式且已驗證基線**：`PROJECT_SPEC.md`、`PROGRESS.md`、`experiment.py`、`svd.py`、`tests/`、`outputs/run-m2/`。這是**JPEG 對全影像 SVD 結構的影響**，並未做浮水印嵌入。
2. **繳交備案**：[PR #7](https://github.com/Rookie-YCLin/matrix-jpeg-research/pull/7) 是 JPEG／SVD 的 11 頁 PDF，未合併、封面仍待填；不得偷偷改題或稱為浮水印成果。
3. **本週已核准的研究主線（G0=A，2026-11-08）**：[Issue #8](https://github.com/Rookie-YCLin/matrix-jpeg-research/issues/8) 是研究方向；[Issue #10](https://github.com/Rookie-YCLin/matrix-jpeg-research/issues/10) 是唯一當前工作包 W0/G1；[Draft PR #9](https://github.com/Rookie-YCLin/matrix-jpeg-research/pull/9) 有管理規範與交接卡。**先原版盲擷取與 JPEG BER baseline，禁止提前改 d2 或生成改良報告**。`PROJECT_SPEC.md` 原始 JPEG/SVD 內容不覆寫。

## 每次任務的執行約定
- 先讀對應 Issue 的**唯一目標、可修改範圍、不可修改項目、驗收條件、停損條件**。研究邊界不清楚，就先在 PR/Issue 報告分歧，**不要擅自啟動另一條演算法研究**。
- 一個分支／PR 只解決一個可驗收問題。先保留上游 baseline，再修改單一主要變因；不可直接推送 `main`，不得擅自合併 PR、覆寫已驗證數據或刪除重要研究資料。
- 不要將歷史 PDF、未驗證 BER、想像中的實驗、只有 pytest 通過的程式宣稱為已證實的研究結論；保留失敗案例及結果限制。
- 提交圖表前檢查 CSV 原始引值、比較對象、誤差定義及圖文可讀性；文字採**問題→為何需要工具→實驗回答→限制**的自然論證，而非規格摘要。
- 回報請用**完成／未完成／驗證證據／阻礙／下一步**，附 commit SHA、PR、命令、CSV 路徑與 CI。
- 新增檔案前先分類為原始資料、程式、必要結果、報告或短期中介。臨時圖／重複 PDF 不應持續堆積。重要檔案的清理需先提案，禁止擅自刪除。

## 原有 JPEG/SVD 重現指令
```sh
python -m pytest -v
python -m experiment --input data/ascent.png --output-dir outputs/run-check --qualities 40 60 80 95
```
使用 `requirements.txt` 的鎖定套件；程式以 Python 3.13 和 float64 計算，8-bit 僅用於可視化影像。CI 於 PR 上執行測試；**CI 成功是技術基礎，不是研究主張通過驗收**。

新浮水印工作目前尚未有完成的實驗腳本與測試；**已授權新分支開始 Issue #10 G1**。不能把上述舊命令誤當水印驗證。
