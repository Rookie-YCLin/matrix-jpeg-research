# 實驗影像來源

`ascent.png` 保存 SciPy `scipy.datasets.ascent()` 的 512×512、8 位元灰階像素，無縮放或額外 JPEG 編碼。SciPy 資料集由原始照片衍生。原始照片作者為 Hillebrand Steve（USFWS），Pixnio 標示 CC0。

- [SciPy 資料集文件](https://docs.scipy.org/doc/scipy/reference/generated/scipy.datasets.ascent.html)
- [SciPy 資料檔](https://github.com/scipy/dataset-ascent)
- [原始照片與使用條件](https://pixnio.com/people/accent-to-the-top)

第一次取得資料需使用網路，日常實驗直接使用本機 PNG。此 PNG 是實驗基準，原始照片曾以 JPEG 發布，影像先前可能已有編碼痕跡。研究比較的是對固定基準再做一次指定 JPEG 編碼後的差異。

PNG 的 SHA-256 為 `3b7cae537bc09699016556df746184a2376083244ae375a2740ee7157970ebf3`。
SciPy 1.18.0 下載的 `ascent.dat` SHA-256 為 `03ce124c1afc880f87b55f6b061110e2e1e939679184f5614e38dacc6c1957e2`。
