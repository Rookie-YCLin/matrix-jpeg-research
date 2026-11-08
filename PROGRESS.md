# 專案進度

## 現行主線與 G2 交接（2026-11-08）

- [Issue #8](https://github.com/Rookie-YCLin/matrix-jpeg-research/issues/8) 恢復盲浮水印主線。W0 與 W0-D 分別交付於 [PR #13](https://github.com/Rookie-YCLin/matrix-jpeg-research/pull/13) 與 [PR #14](https://github.com/Rookie-YCLin/matrix-jpeg-research/pull/14)，固定提交的 Research CI 已通過，兩者待人工研究驗收。
- [實驗索引](docs/EXPERIMENT_INDEX.md) 保存證據與重跑方式。[Issue #16](https://github.com/Rookie-YCLin/matrix-jpeg-research/issues/16) 是唯一 G2 工作入口，待主持人批准。此次僅整理文件，G2 未執行。
- 既有 M0–M4、[PR #7](https://github.com/Rookie-YCLin/matrix-jpeg-research/pull/7)、[PR #12](https://github.com/Rookie-YCLin/matrix-jpeg-research/pull/12) 及 [PR #15](https://github.com/Rookie-YCLin/matrix-jpeg-research/pull/15) 保留。AI 審查暫不啟用。

## 2026-11-07

- 研究計畫第二版已核准。M0 與 M1 開始執行。
- 起始工作目錄為空，Python 3.13.14 可用。建立隔離環境，準備固定實驗輸入。
- 首次取圖命令在套件安裝仍進行時啟動，SciPy 匯入失敗。安裝完成後重跑成功，`pip check` 無相依錯誤。
- M0 完成。已保存 `data/ascent.png`、來源及 SHA-256，並以 `requirements.txt` 鎖定套件。
- M1 正式執行通過。首輪 `python -m pytest -q` 為 8 通過、0 失敗、0 跳過，紀錄位於 `outputs/pytest.txt`。

## M1 驗收證據

正式輸出位於 `outputs/run-001`。三張圖已目視檢查，六組重建 PNG 和圖檔均通過測試讀取。

| 輸出 | 內容 |
|---|---|
| `manifest.json` | 資料雜湊、環境、JPEG 設定、驗證誤差及檔案索引 |
| `rank_*.png`、`reconstructions.png` | 六組 Rank-k 重建與原圖、解碼圖拼圖 |
| `rank_errors.csv`、`rank_errors.png` | 兩張圖各自的平方殘差、尾端平方和與誤差曲線 |
| `spectrum.csv`、`spectra.png` | 各 512 項奇異值和累積平方能量 |
| `jpeg_q80.jpg`、`jpeg_decoded.png`、`jpeg_metrics.csv` | 實際 JPEG、解碼像素與品質量測 |

- 原圖與解碼圖的正規化平方殘差對尾端平方和之最大絕對差分別為 2.22e-16 與 3.33e-16。兩圖的誤差皆隨 k 非遞增。
- k=100 時，原圖與解碼圖相對各自的平方 Frobenius 誤差分別為 0.51677% 與 0.53177%。對應的前 100 項平方能量占比為 99.48323% 與 99.46823%。
- Q=80 的實際檔案大小為 45,222 bytes。解碼相對輸入 MSE 為 10.26691，PSNR 為 38.01641 dB。兩條頻譜在前段接近，尾段差異較可見。

## 重跑命令

從專案根目錄使用 PowerShell。輸出目錄須是新目錄。

```powershell
py -3.13 -m venv .venv-local
$python = '.\.venv-local\Scripts\python'
& $python -m pip install -r requirements.txt
& $python -m pip check
& $python -m experiment --input data/ascent.png --output-dir outputs/run-local
& $python -m pytest -q
```

已用全新的 `.venv-replay` 安裝鎖定依賴，`pip check` 通過，重跑至 `outputs/run-replay`。第二輪測試為 8 通過、0 失敗、0 跳過，見 `outputs/pytest-replay.txt`。兩次執行的輸入 SHA-256 一致，14 個受索引的輸出檔（含三個 CSV）SHA-256 逐檔相同，見 `outputs/replay-comparison.txt`。驗證範圍為同一台 Windows 主機的兩個獨立環境。

M0、M1 技術驗收完成，無未修復的測試失敗。交付後，使用者指示「請延續既定的 M2 實驗計畫」，並要求自 M2 起在獨立分支開發、測試後推送及開 PR。此指令解除 M1 階段的等待，允許進入既定的 M2 多品質比較與原始方向投影，交付後仍須經 PR 人工驗收。未經使用者批准，禁止合併至 main 或進入 M3。

## 2026-11-08 M2 多品質比較

- 在 `research/m2-jpeg-comparison` 完成四品質獨立編解碼與共用原圖基底的投影。M0、M1 輸出保留。預設命令仍執行單次 Q=80。
- 重跑命令為 `python -m experiment --input data/ascent.png --output-dir outputs/run-m2-local --qualities 40 60 80 95`。
- 技術驗收通過，下一步為 GitHub PR 審查。最終書面報告留待後續里程碑。

### 實驗與驗收

- 同一張 512×512 灰階 `ascent` 各自以 Q=40、60、80、95 編碼，重新解碼後計算各自的 SVD 與低秩誤差。原圖只分解一次，四組投影共用其秩一方向。
- M2 初次執行的 `python -m pytest -q` 有 11 項通過。Research CI 擴充存檔驗證後，`python -m pytest -v` 有 13 項通過、0 項失敗、0 項跳過。測試交叉核對投影與 Frobenius 內積、實際解碼像素與頻譜、JPEG 檔案大小及新圖的繪圖資料。Q=80 的 JPEG 位元組和品質指標與 M1 一致。
- 五個矩陣的 Frobenius 正規化平方殘差恆等式最大差為 1.11e-15，見 [執行紀錄](outputs/run-m2/manifest.json)。

| JPEG Q | 實際大小（bytes） | MSE | PSNR（dB） | Rank-100 相對平方誤差 |
|---:|---:|---:|---:|---:|
| 40 | 23,780 | 37.09696 | 32.43742 | 0.46522% |
| 60 | 30,965 | 23.62286 | 34.39748 | 0.52460% |
| 80 | 45,222 | 10.26691 | 38.01641 | 0.53177% |
| 95 | 89,876 | 1.62239 | 46.02924 | 0.52482% |

來源為 [JPEG 指標](outputs/run-m2/jpeg_metrics.csv) 各 Q 的 jpeg_bytes、mse、psnr_db，以及 [低秩誤差](outputs/run-m2/rank_errors.csv) 各解碼圖 k=100 的 relative_squared。原圖同一欄為 0.51677%。此案例中，Q 越高，PSNR 與檔案大小越高，Rank-100 相對平方誤差則未呈單調變化。Rank-100 誤差以各矩陣自身為基準，PSNR 以原圖為基準。

[投影表](outputs/run-m2/projections.csv) 中 i=1 的 delta 依 Q 順序約為 +67.47546、+5.91717、+0.41804、−1.93513。[投影圖](outputs/run-m2/projections.png) 保留正負號。

### 研究限制與待審查

- 結果限於單張影像和鎖定版本的編解碼器。Q 是編碼設定，位元組是實測儲存成本。
- 請審查 `c_i = u_iᵀ B v_i` 的索引與符號，以及它與 B 的奇異值、資訊保留率的區別。遇到重複奇異值時，個別係數依賴選用的原圖基底。
- 請確認各自低秩誤差與相對原圖的像素品質分開解讀，並核對 [頻譜](outputs/run-m2/spectra.png)、[大小與 PSNR](outputs/run-m2/jpeg_metrics.png) 及 [測試紀錄](outputs/pytest-m2.txt)。

### M2 PR 自動驗收

- PR 建立、更新分支或重新開啟時觸發 Research CI。在 GitHub 標準 Ubuntu runner 安裝鎖定依賴，記錄 Python、套件與 Pillow 編解碼器版本，執行 `python -m pytest -v`。
- 沿用既有數學驗收，另逐項檢查 M2 存檔與重跑的 CSV、投影和品質圖的繪圖資料、圖檔與 manifest。Q=80 仍核對 M1 相容性，分別比較同次環境重新編碼的資料以及已提交的兩份存檔。
- 在 PR 的 Checks 查看逐項 PASS 或 FAIL，展開失敗步驟保留錯誤。修正後在原分支重跑並推送。使用 PR 範本記錄繁中驗收摘要。
- [外部補充審查](https://github.com/Rookie-YCLin/matrix-jpeg-research/pull/1#issuecomment-6709916235) 確認 [Research CI](https://github.com/Rookie-YCLin/matrix-jpeg-research/actions/runs/42391388981) 技術驗收通過，並要求補記 M1 至 M2 的授權與現行審查門檻。本次僅同步文件，M2 仍待 PR 人工驗收。

## 2026-11-08 M3 分析草稿

- M2 已完成外部技術驗收，並經使用者批准將 [PR #1](https://github.com/Rookie-YCLin/matrix-jpeg-research/pull/1) 合併至 main，提交為 `02d462e419f58f852e2c0b7c2353880b9f0da726`。
- 依 [Issue #2](https://github.com/Rookie-YCLin/matrix-jpeg-research/issues/2) 從最新 main 建立 `research/m3-analysis`，交付 [M3 分析與答辯草稿](reports/M3_ANALYSIS.md)。已逐圖核對，並以現有四份 CSV 交叉核對 PSNR、檔案大小、能量、尾端誤差、投影差值及文中引值。
- 本機 `python -m pytest -v` 為 13 通過、0 失敗、0 跳過。原有實驗程式、測試與存檔均保留。
- M3 交付後等待 PR 人工研究審查。M4 正式書面報告、引用核對與重現驗收留待批准。題目與教師的確認選項已列入草稿。

## 2026-11-08 M4 正式交付

- M3 已完成研究驗收，[PR #3](https://github.com/Rookie-YCLin/matrix-jpeg-research/pull/3) 已合併至 main（`3f8223b3d77c7342eb85403a98d1135f12b1fa82`）。M4 依 [Issue #4](https://github.com/Rookie-YCLin/matrix-jpeg-research/issues/4) 從該基線建立 `research/m4-final-report`。
- 交付 [正式報告](reports/FINAL_REPORT.md)、[答辯稿](reports/DEFENSE_NOTES.md)及[最終核對紀錄](reports/FINAL_CHECKLIST.md)。已核對公式、四份 M2 CSV 引值、文獻、五張圖與相對路徑。
- 在另一個 Windows 隔離環境重跑 M2 至新暫存目錄。兩份 CSV 有浮點末位差異，已通過數值容差核對，差異詳見最終核對紀錄。本機 `python -m pytest -v` 為 13 通過、0 失敗、0 跳過。
- M4 待外部研究審查及使用者批准合併。正式題目、繳交格式與封面資料仍待確認。
