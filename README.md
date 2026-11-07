# Matrix JPEG Research｜研究室入口

這是私有的矩陣理論與影像處理課程研究倉庫。**請先辨別「已驗證的舊研究」與「G0 已核准、正在開始的水印研究」**，不要把兩者的證據混在一起。

## 現在的狀態

| 路線 | 位置 | 事實與限制 |
|---|---|---|
| **已驗證：JPEG 對影像 SVD 結構的影響** | `main`、`PROJECT_SPEC.md`、`outputs/run-m2/` | 原圖與 JPEG 解碼圖的奇異值、低秩誤差、固定原圖方向投影；**不是浮水印實驗** |
| **正式 PDF 交件備案** | [PR #7](https://github.com/Rookie-YCLin/matrix-jpeg-research/pull/7) | 舊 JPEG/SVD 11 頁報告經有條件驗收；封面待填；保持 open、不可混作水印成果 |
| **本週已核准主線（G0=A）：盲浮水印抗 JPEG** | [Issue #8](https://github.com/Rookie-YCLin/matrix-jpeg-research/issues/8)、[Issue #10](https://github.com/Rookie-YCLin/matrix-jpeg-research/issues/10) | 已授權 G1 **原版 baseline**；目前尚無可重現的新 BER，不准跳到 G2 |
| **研究管理規範** | [Draft PR #9](https://github.com/Rookie-YCLin/matrix-jpeg-research/pull/9) | 研究者已決策 G0=A；管理文件仍是草稿 PR，尚未合併 `main` |

## 對三人研究室的導航

**研究者**：決定問題、限制與是否接受結論；不需要每天管理分支。

**Codex**：開工先讀 `AGENTS.md`，再讀本次 Issue；若任務涉及提議中的水印方向，須讀 `docs/ONE_WEEK_RESEARCH_CHARTER.md` 與 `docs/CODEX_NEXT_SESSION.md`（目前位於 PR #9 分支，還不在 `main`）。**目前只做 Issue #10 的原版 baseline**。

**ChatGPT**：管理 Issue／PR，對數學、數據、實驗公平性、圖表及報告做獨立審查；審查意見留在 PR Conversation。CI 通過不代表研究結論有效。

## 研究材料在哪裡？

| 類別 | 目前路徑 | 使用原則 |
|---|---|---|
| 研究規格與紀錄 | `PROJECT_SPEC.md`、`PROGRESS.md` | 目前正式生效的是 JPEG／SVD 範圍 |
| 程式與測試 | `experiment.py`、`svd.py`、`imaging.py`、`charts.py`、`tests/` | 以鎖定環境和實測輸出為準 |
| 原始影像 | `data/ascent.png`、`data/README.md` | 輸入來源、SHA 與重跑保持可追溯 |
| 實驗數據 | `outputs/run-m2/` | JPEG Q40/60/80/95 對照，勿覆寫 |
| 研究分析／已合併文字 | `reports/M3_ANALYSIS.md`、`reports/FINAL_REPORT.md` | 已合併版本，與 PR #7 的進階排版不同 |
| 一週水印研究章程 | `docs/ONE_WEEK_RESEARCH_CHARTER.md`（PR #9） | **G0 已核准 A；G1 尚待實測**，不是已驗收實驗 |

## 重現既有研究

```sh
python -m pip install -r requirements.txt
python -m pytest -v
python -m experiment --input data/ascent.png --output-dir outputs/run-check --qualities 40 60 80 95
```

Python 3.13；請用新輸出目錄，不要直接覆寫 `outputs/run-m2/`。跨環境 JPEG 位元組可能不同，必須記錄版本及相容性。

## 最小協作流程

研究問題寫進 **Issue** → Codex 獨立分支做單一任務 → **PR** 提供修改與數據來源 → CI 和 ChatGPT 審查 → 研究者決定是否接受及合併。

- **一個 PR 一個問題**：先能重現、再談改良；不把實驗計畫寫成已驗證結果。
- **不要堆檔案**：保留能重建圖表的資料、程式和最終圖；中介物與重複版 PDF 不應大量提交。
- **不要清除歷史**：整理先列保留／歸檔／候選刪除提案，研究者批准才刪除已驗證資料。
- **報告目標**：數學可理解、圖表有研究主張、觀察與推測清楚區分，而非只滿足頁數與字型。

參考工作原則：[OpenAI Codex best practices](https://learn.chatgpt.com/docs/learn/best-practices)、[OpenAI Cookbook：Iterating development workflows](https://github.com/openai/openai-cookbook/blob/main/examples/codex/iterating-development-workflows-with-codex.md)、[The Turing Way：Research Compendia](https://book.the-turing-way.org/reproducible-research/compendia/)。
