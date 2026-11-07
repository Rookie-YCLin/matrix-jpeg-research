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

M0、M1 技術驗收完成，無未修復的測試失敗。待人工確認研究方法與初步結果。通過後才進行多品質比較與原始方向投影。
