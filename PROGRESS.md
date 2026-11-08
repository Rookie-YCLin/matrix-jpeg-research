# 專案進度

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

## W0／G1 原版盲浮水印基準

- 依 [Issue #10](https://github.com/Rookie-YCLin/matrix-jpeg-research/issues/10) 從 `origin/main` 建立 `codex/w0-watermark-baseline`。凍結三張 RGB PNG 與固定 32-bit payload，使用固定提交的公開 bit 介面、common 模式和 d1=36、d2=20。上游及歷史實驗程式與輸出保留。
- 無攻擊三圖各 0/32。Q40、Q60、Q80、Q95 各合計 0/96。含浮水印 PNG 相對原圖 PSNR 為 37.59–38.20 dB。JPEG 解碼相對原圖的 PSNR 範圍依 Q 分別為 29.88–32.24、31.03–33.35、32.90–34.78、36.05–36.87 dB。
- Python 3.13.14 隔離環境的 `pip check` 通過，原有 13 項與新增 5 項測試共 18 通過。兩次獨立輸出核對 17 個檔案，SHA-256 全數相同。逐位結果、manifest 與 OpenCV 建置資訊見 [正式輸出](outputs/run-w0)，另有 [重跑輸出](outputs/run-w0-repeat)、[比對結果](outputs/w0-replay-comparison.json) 及 [pytest 紀錄](outputs/pytest-w0.txt)。
- 安裝及存檔失敗原因、修正與上游 PNG writer 提示見 [執行診斷](watermark_baseline/DIAGNOSTICS.md)。Research CI 沿用舊測試，另安裝 W0 鎖定依賴並於 runner 重跑 W0。
- 待審查固定影像代表性與 BER 下限。每個品質只有三張圖、單一 payload 共 96 位元，且 JPEG 固定 4:4:4。是否進入 G2 由研究主持人決定。

## W0-D JPEG 壓力診斷

- 從 [W0 PR #13](https://github.com/Rookie-YCLin/matrix-jpeg-research/pull/13) 的固定提交建立診斷分支，直接使用 W0 存檔 PNG。六個條件共 18 組逐圖結果與 576 筆位元分數，保存於 [正式輸出](outputs/run-w0-d)。
- Q10、4:4:4 合計 12/96，Q20、4:4:4 為 78/96。其他四組各 0/96。Chelsea 在 Q10 零錯誤但有一位距中點約 0.000156。Coffee 在 Q20 全位元反轉。錯誤位置、PSNR、JPEG 大小及候選條件見 [診斷結論](watermark_baseline/STRESS.md)。
- 完整 pytest 21 項通過。兩次新目錄的 21 個索引檔案 SHA-256 全數一致，見 [比對紀錄](outputs/w0-d-replay-comparison.json)。CI 另以 runner 自身 codec 重跑。
- 待審查 Q10 是否列為後續主要候選，Q20 是否單列為高壓失效案例。

## G2｜第二奇異值嵌入強度

- 基底為 W0-D PR #14 的 `168e5070cacbdeeaefab58ed469dd7e90db4aa3f`，承接 W0 PR #13。比較 d2=10、20、30，三張圖各自獨立嵌入及編碼 Q10、Q20、Q30，皆為 4:4:4。
- 所有無攻擊 PNG 與 Q30 皆零錯誤。主要條件 Q10 的錯誤數依 d2 為 18、12、19（各 96 位元）。d2=10 三圖皆符合 PNG PSNR ±1.0 dB，Q10 仍逐圖多錯 2 位。Q20 的 astronaut 少錯 4 位，屬失效案例的局部改善。
- d2=20 與兩份歷史基準的 12 項對應結果在 Windows 上逐位、PSNR 和 SHA-256 一致。兩份新目錄的 41 個索引檔案完全相同。
- 逐位 CSV、配對差異、分數、圖與 manifest 位於 [正式輸出](outputs/run-g2)，重跑存於 [第二份輸出](outputs/run-g2-repeat)。報告摘要與限制見 [G2 文件](watermark_baseline/G2.md)。完成後停止擴張實驗，交由主持人審查與後續報告使用。
