# W0／G1 原版盲浮水印基準

工作規格見 [Issue #10](https://github.com/Rookie-YCLin/matrix-jpeg-research/issues/10)。三張 RGB PNG 從 scikit-image v0.26.0 原樣保存，來源、授權、尺寸與 SHA-256 見 [輸入清單](../data/w0/inputs.json)。樣本在計算 BER 前凍結。

以 [固定上游提交](https://github.com/guofei9987/blind_watermark/tree/322c90dc02d45644692095b34d3a6b735b6edbd8) 安裝原始套件，MIT 授權見 [LICENSE.upstream](LICENSE.upstream)。上游的 `bwm_core.py`、`blind_watermark.py` Git blob 分別是 `092242a37d975e0b26fa9608810d05f8ab0983b4`、`eea10ed18c28dd7711a4dc890fbce80506e322c9`。執行時核對已安裝套件的提交。使用上游預設的 common、`fast_mode=False`、4×4、d1=36、d2=20，透過公開 bit 介面嵌入和擷取。擷取器只接收測試影像、32 位元長度和事前固定的設定。原始 payload 在擷取後才用來比對。

## 重跑

從專案根目錄執行，兩個輸出目錄都必須是新目錄。Windows 下使用 ASCII 相對輸出路徑供上游 OpenCV PNG writer 使用。

```powershell
py -3.13 -m venv .venv-w0-review
$p = '.\.venv-w0-review\Scripts\python.exe'
& $p -m pip install -r requirements-w0.txt
& $p -m pip install --no-build-isolation -r watermark_baseline/upstream.txt
& $p -m pip check
& $p -m watermark_baseline --output-dir outputs/run-w0-review
& $p -m watermark_baseline --output-dir outputs/run-w0-review-repeat
& $p -m watermark_baseline.compare_runs outputs/run-w0-review outputs/run-w0-review-repeat
& $p -m pytest -v
```

上游 `setup.py` 在建置時匯入執行依賴，因此先安裝鎖定依賴，再安裝上游。兩次輸出比較使用同一套環境，逐檔核對 SHA-256 和 manifest，僅排除含輸出路徑的命令欄。

## 數據解讀

無攻擊 PNG 從磁碟讀回後才盲擷取。任一影像有錯誤位元或擷取警告時，程式保存已取得的 PNG 與逐位紀錄並停止 JPEG 階段。可用相同命令指定全新目錄重現。通過後，每個 JPEG Q 各自從同一 PNG 編碼，並以重新解碼的 RGB 像素擷取。

`results.csv` 的 `psnr_marked_db` 比較原圖和含浮水印 PNG，`psnr_jpeg_vs_original_db` 比較原圖和 JPEG 解碼影像。後者含嵌入與 JPEG 的總失真。兩欄均對全部 RGB 像素與通道計算 MSE，以 255 為峰值。錯誤位置從 1 開始，BER 為錯誤數除以 32，使用原版 k-means 與位元順序還原。每圖一個固定 payload，每個品質合計 96 位元。結果限於此組圖、payload、密鑰、原版參數與編解碼器設定。
