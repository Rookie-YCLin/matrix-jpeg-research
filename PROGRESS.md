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

## R1｜原圖秩一方向的分塊 DCT 與 JPEG 量化步長

- 依 [Issue #11](https://github.com/Rookie-YCLin/matrix-jpeg-research/issues/11) 與 [開工交接](https://github.com/Rookie-YCLin/matrix-jpeg-research/issues/11#issuecomment-6713144151)，從 `origin/main` 的 `ede4ce330b2e21790cacf3bb6fed879e8b79ec67` 建立 `codex/r1-svd-dct-sensitivity`。已讀 Draft PR #9 在 `e3e613a50a1ef1eb4efb71938c8193902eb915cf` 的交接卡、章程與 AGENTS.md。工作樹乾淨，基線 13 項測試通過。
- 固定原始 512×512 灰階 PNG 與四張 M2 JPEG 的 SHA-256。依 JPEG [ITU-T T.81](https://www.itu.int/rec/T-REC-T.81/en) 的 SOF0 分量選擇器及 DQT zigzag 掃描座標，獨立核對 Pillow 12.3.0 的自然列序。四張均為分量 ID 1、量化表 ID 0、8 位元正值，64 個座標全部相等。兩種排列及各檔案雜湊保存在 manifest。
- 對 512 個方向完成 float64 分塊正交 DCT-II，未做位準平移。每個 8×8 的 W 皆非負，總和偏離 1 的最大值為 3.774758283725532e-15（絕對容差 1e-12）。`weights.npy` 的索引為 `[i-1, k, l]`，k 垂直、l 水平。CSV 有 2048 列 `i,sigma_i,Q,S_i`。
- 同一鎖定環境在兩個新目錄獨立執行。W、奇異值及 S 的最大絕對差均為 0，兩份數值產物的 SHA-256 也逐一相同。比較容差 rtol=1e-8、atol=1e-12。見[主執行 manifest](outputs/run-r1/manifest.json)、[第二次 manifest](outputs/run-r1-replay/manifest.json)及[比較證據](outputs/r1-replay-comparison.json)。
- 本機 Python 3.13.14、NumPy 2.4.6、SciPy 1.18.0、Pillow 12.3.0、JPEG codec 8.0（libjpeg-turbo 3.1.4.1）。`pip check` 通過，完整測試 27 通過、0 失敗、0 跳過，含原有 13 項。見[逐項測試](outputs/r1-pytest.txt)。GitHub Research CI 的逐項證據見 R1 PR 的 Checks。
- S 是以量化步長加權的頻譜量；重複奇異值子空間的個別方向依基底而定。R1 待審查，實際誤差關係留待另獲授權的 R2。本輪沒有浮水印或 BER 實驗。

從專案根目錄重跑，輸出路徑必須為新目錄，`--report` 亦須指定新檔名。

```powershell
py -3.13 -m venv .venv-r1
$python = '.\.venv-r1\Scripts\python.exe'
& $python -m pip install -r requirements.txt
& $python -m pip check
$env:OPENBLAS_NUM_THREADS = '1'
& $python -m analysis.r1 --input data/ascent.png --jpeg-dir outputs/run-m2 --output-dir outputs/run-r1-local
& $python -m analysis.r1 --input data/ascent.png --jpeg-dir outputs/run-m2 --output-dir outputs/run-r1-local-replay
& $python -m analysis.compare_r1 outputs/run-r1-local outputs/run-r1-local-replay --report outputs/r1-local-comparison.json
& $python -m pytest -v
```

## 2026-11-08 M4 正式交付

- M3 已完成研究驗收，[PR #3](https://github.com/Rookie-YCLin/matrix-jpeg-research/pull/3) 已合併至 main（`3f8223b3d77c7342eb85403a98d1135f12b1fa82`）。M4 依 [Issue #4](https://github.com/Rookie-YCLin/matrix-jpeg-research/issues/4) 從該基線建立 `research/m4-final-report`。
- 交付 [正式報告](reports/FINAL_REPORT.md)、[答辯稿](reports/DEFENSE_NOTES.md)及[最終核對紀錄](reports/FINAL_CHECKLIST.md)。已核對公式、四份 M2 CSV 引值、文獻、五張圖與相對路徑。
- 在另一個 Windows 隔離環境重跑 M2 至新暫存目錄。兩份 CSV 有浮點末位差異，已通過數值容差核對，差異詳見最終核對紀錄。本機 `python -m pytest -v` 為 13 通過、0 失敗、0 跳過。
- M4 待外部研究審查及使用者批准合併。正式題目、繳交格式與封面資料仍待確認。
