# W0 執行診斷

- 初次並行安裝時，兩個 pip 程序寫入同一隔離環境，Windows 回報 `[WinError 32]`，鎖定檔為 `numpy/_core/tests/test_item_selection.py`。改用全新隔離環境並依序安裝。
- 只預裝 setuptools 後，從固定 Git 提交準備套件 metadata 時回報 `ModuleNotFoundError: No module named 'numpy'`。上游 `setup.py` 會匯入 `blind_watermark`，其公開介面載入 NumPy。最小重現為在乾淨 Python 3.13 venv 只裝 `setuptools==84.2.1`，再執行 `python -m pip install --no-build-isolation -r watermark_baseline/upstream.txt`。依 README 改為先安裝全部鎖定依賴，安裝成功，`pip check` 通過。上游程式維持原版。
- 加入存檔驗收後，在正式輸出尚未產生時先跑完整測試。結果為 17 通過、1 失敗，失敗是 `test_archived_results` 找不到 `outputs/run-w0/manifest.json`。
- 第一次完整執行在寫 manifest 時回報 `TypeError: Object of type int64 is not JSON serializable`。區塊容量轉成 Python `int` 後，從兩個新目錄重跑。此修正僅影響記錄型別。首次 CSV 與影像留存於本機暫存備查。
- 每次原版 PNG writer 首次寫檔時，OpenCV 提示 `Unsupported depth image for selected encoder is fallbacked to CV_8U`。保留原版 float32 寫檔行為。回讀 PNG 為 RGB uint8，三張圖的原版盲擷取各為 0/32，擷取未發出 Python 警告。
