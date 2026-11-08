# G6｜固定血小板影像的 QF15 BER 與 PSNR

## 實驗設定

沿用 [G6 封存驗證](G6_SVD_QIM_QF15_SUCCESS.md)。唯一輸入為上游固定提交的 `examples/pic/ori_img.jpeg`，Git blob `ef48a056b3cab1d2c08723c014d8d515963f5a07`，SHA-256 `17bed8cfeb5534351d2f35d4addd9407e0c0132132444276a0f826c7ae9923c2`。Pillow 解碼陣列為高 1108、寬 738、三通道 RGB uint8。PSNR 以這份 JPEG 的解碼像素為基準。

原版 (36,20) 與 G6 (90,20) 分別嵌入同一 32-bit payload，兩把密鑰皆為 1。使用上游 full SVD，嵌入及擷取的步長同步。兩組各自寫出 PNG，再從磁碟讀取 PNG，以 Pillow QF15、4:4:4、subsampling=0、optimize=False、progressive=False 編碼。對四份產物重新解碼，再量測 RGB 影像。盲擷取使用公開 bit 介面，正確 payload 只在擷取後核對。

## 實測

| 量測階段（均相對原圖解碼） | 原版 MSE | G6 MSE | 原版 PSNR | G6 PSNR | G6 − 原版 |
|---|---:|---:|---:|---:|---:|
| 嵌入後、未受 JPEG 攻擊的 PNG | 9.396396 | 42.950692 | 38.401 dB | 31.801 dB | −6.600 dB |
| 嵌入後、QF15 JPEG 攻擊 | 77.730415 | 114.211263 | 29.225 dB | 27.554 dB | −1.671 dB |

兩張 PNG 均為 0/32 錯誤。QF15 的 BER 從原版 **100%（32/32）** 降至 G6 **0%（0/32）**，與封存結果逐位相同，兩份 QF15 JPEG 的 SHA-256 也各自吻合封存。此次 PNG 的位元組雜湊與歷史 PNG 不同。此處採 Windows 上 OpenCV 的 PNG 記憶體編碼，歷史流程透過上游寫檔，兩種差異來源未分離。沒有使用歷史 PNG 像素替代本次量測。兩次本機獨立執行的六個索引檔案（原圖、兩張 PNG、兩張 JPEG、CSV）SHA-256 逐檔相同。[完整精度 CSV](../outputs/svd-qim-psnr-qf15/results.csv) · [輸入、產物與版本 manifest](../outputs/svd-qim-psnr-qf15/manifest.json)

MSE 是全部 RGB 樣本的 float64 平方差平均，即 `sum((I−J)^2)/(3HW)`。8-bit 峰值為 255，PSNR 為 `10 log10(255^2/MSE)`，MSE=0 時為正無限大。QF15 後 PSNR 同時反映嵌入與 JPEG 攻擊後的像素差異。兩階段的 dB 差無法拆成可加的失真成分。

這張圖在固定設定下，G6 的 BER 改善伴隨可量測的像素品質代價。結果限於此圖、payload、QF15、金鑰和編碼設定。較大的第一奇異值步長提高理想局部判決裕度，但不保證其他影像的 BER 或 PSNR 會有相同變化。

## 重現與驗證

使用 Python 3.13 隔離環境，在專案根目錄執行。輸出目錄須尚不存在。程式從固定上游提交下載原圖，驗證兩種雜湊後才進行嵌入。影像可由命令重新產生，版本庫保留量測 CSV 與 manifest。

```text
python -m pip install -r requirements.txt
python -m pip install opencv-python==4.13.0.92 PyWavelets==1.10.0 setuptools==84.2.1
python -m pip install --no-build-isolation "blind_watermark @ git+https://github.com/guofei9987/blind_watermark.git@322c90dc02d45644692095b34d3a6b735b6edbd8"
python -m pip check
python -m experiments.svd_qim_psnr --output-dir outputs/g6-psnr-review
python -m experiments.svd_qim_psnr --output-dir outputs/g6-psnr-review-repeat
python -m pytest -v
```

對照兩個 manifest 的 `files_sha256`。本機 pytest 共 21 項通過，耗時 11.21 秒。測試包括滿幅 RGB 差、uint8 減法溢位、三通道平均、零誤差、尺寸與型別拒絕、封存 CSV 公式與 BER 一致性。開發時先更正一筆手算測試預期值（26.370678 → 26.369891018122292 dB），再更正影像高寬順序（738×1108 → 1108×738，以高×寬表示）。兩次均在實驗嵌入前中止並重跑。此 PR 的 Research CI 跳過舊候選和全品質掃描，另以同一固定 QF15 重跑，保留完整 pytest。
