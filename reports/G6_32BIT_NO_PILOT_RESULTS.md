# G6 極低 JPEG QF：固定 32-bit、無 Pilot 的盲式擷取改善（探索性研究）

> 2026-11-09。此為獨立的後續實驗，不取代已封存的 G6 d1=90/d2=20 QF15 BER/PSNR 正式結論。所有數字為 GitHub Actions 實測，不是理論預測。

## 1. 研究問題與固定條件

- 原始圖片：guofei9987/blind_watermark 的 examples/pic/ori_img.jpeg；固定原圖 Git blob、32-bit、密鑰 password_img=password_wm=1。
- 上游演算法提交：322c90dc02d45644692095b34d3a6b735b6edbd8；DWT(Haar)-4×4 DCT-洗牌-SVD-QIM；三個 YUV 通道、重複區塊投票，fast_mode=False。
- G6：d1=90、d2=20；JPEG：Pillow、4:4:4 (subsampling=0)、optimize=False、progressive=False。
- 遵守 32 個有效資料位元、不額外嵌入 Pilot、解碼器不能知道正確位元或利用 BER 做選擇。
- 主要變體只修改擷取；其所有實驗直接使用相應 G6 所產生的 32-bit marked PNG，因此嵌入像素／PSNR 與 G6 不變。

## 2. 直接觀察

固定主資料 32 bits：QF1～4 全部 0/32、QF5～7 全部 32/32、QF8=22/32、QF9～15 全部 0/32。這並非 BER 隨 JPEG QF 單調上升。QF5～7 輸出是逐位反碼，並不能因此宣稱 JPEG 破壞了所有資訊。

逐層分析顯示 QF5～8 第一奇異值投票的平均位元分數差由正轉負，第二奇異值仍呈正向但較弱。第二奇異值因此可用於估計第一奇異值的方向，但不保證在不同圖片／攻擊下仍成立。

## 3. 無 Pilot 的盲式自校正解碼器

設 H1、H2 為原演算法對應奇異值的逐區塊硬判決（0/1）經通道、重複嵌入平均，以及正確反洗牌後的 32 維分數；令 b1=KMeans(H1)、b2=KMeans(H2)。

自校正方向完全取決於接收到的兩個估計序列：

```text
agreement = sum(b1[j] == b2[j] for j in range(32))
flip = (agreement < 16)  # 恰好 16 時不反轉
```

接著對兩個奇異值的各個區塊使用連續 QIM 分數，而非立刻丟棄餘數資訊：

```text
soft_i(sigma_i) = (1 - sin(2*pi*(sigma_i mod d_i)/d_i)) / 2
```

將 soft1、soft2 同樣跨區塊／通道平均並對位元反洗牌得到 T1、T2。若 flip=True，令 T1_corrected=1-T1；否則 T1_corrected=T1。最後輸出：

```text
decoded_32bit = KMeans(0.75*T1_corrected + 0.25*T2)
```

此方法不需 QF、不需原圖、不需原始 32-bit 真值、也不增加參考位元；第二奇異值充當已存在的內部方向線索。解碼器透過觀測的硬位元一致性決定整體極性，之後用連續 QIM 分數處理局部錯誤。

## 4. 首輪三組 32-bit 資料：方法比較

| 候選（固定同一影像，QF1～15、20、25、30、40、50、70、95） | 全部錯誤位元合計 | QF5～8之外的錯誤 |
|---|---:|---:|
| 原始 G6 | 349 | 0 |
| 固定權重 1:1 | 327 | 0 |
| 固定權重 sigma1:sigma2=1:3 | 264 | 有（如 QF3） |
| 僅使用 sigma2 硬判決 | 213 | 有（包括 QF≥10） |
| sigma1 整體極性自校正（硬判決） | 20 | 0 |
| 校正極性後融合 sigma1、sigma2 硬判決 | 7 | 0 |
| **校正極性後融合 sigma1、sigma2 連續 QIM 分數** | **4** | **0** |
| 僅做軟判決、不做極性校正 | 384 | 0 |
| 奇異值差值 sigma1−sigma2 的 QIM（需重嵌入） | 331 | 0 |

本表有三組不同的 32-bit 位元序列（主序列、另一組、主序列的反碼），每組 22 個 JPEG QF 點，合計 3×22×32=2112 個逐點評估位元。不同 QF 與位元之間高度相關，不能將 2112 視為獨立樣本。

## 5. 凍結規則後的額外四組 32-bit 序列驗證

在首輪選出軟判決自校正後，另以預定 RandomState seeds 20261109、20261110、20261111、20261112 各產生新的 32-bit 序列，不再修改方法。QF 取 1、4、5、6、7、8、9、10、11、15、20、95。

| QF | 原始 G6 錯誤（四組合計） | 自校正軟判決錯誤（四組合計） |
|---|---:|---:|
| 5 | 126/128 | 0/128 |
| 6 | 128/128 | 0/128 |
| 7 | 128/128 | 0/128 |
| 8 | 84/128 | 10/128 |
| 已測 1、4、9、10、11、15、20、95 | 0 | 0 |

四組新資料在 QF8 的改善後錯誤數分別為 4、2、2、2/32。QF5～7 均為 0/32，已測 QF≥10 亦均為 0/32。

## 6. 七組累計結果（非七張不同圖片）

| QF | G6 原始錯誤（七組共 224 bits） | 自校正軟判決錯誤 |
|---|---:|---:|
| 5 | 220 | **0** |
| 6 | 224 | **0** |
| 7 | 224 | **0** |
| 8 | 147 | **14** |
| 四個異常 QF 合計 | **815/896** | **14/896** |

因此本固定樣本的 QF5～8 合計 BER 從 90.96% 降至 1.56%；QF8 單獨由 147/224（65.625%）降至 14/224（6.25%）。這不是對所有 JPEG 品質或所有圖片的保證。

## 7. 失敗方案與研究限制

- 固定改權重與單獨採用 sigma2，雖可降低部分低 QF BER，卻可能損失其他 QF 原有的零錯誤結果。
- 單純 QIM 軟判決在反相區間仍然無法消除方向錯誤；必須先利用內部兩路估計決定方向。僅依軟分數相關係數判斷反轉，在本次實測也失敗。
- 修改嵌入器將 sigma1−sigma2 做 QIM 沒有解決 QF5～8，因此不推薦在目前固定目標下取代 G6。
- 無 Pilot 的方向判斷依賴 sigma2 提供相對可靠的極性線索。如果 sigma1 與 sigma2 同時反轉，或 sigma2 嚴重受損，不能保證自校正有效。沒有額外資訊時，本質上可能有 W 與其反碼的辨識歧義。
- 僅一張固定圖片、七組 32-bit 序列、指定 JPEG 編碼器與 QF 點；沒測試其他圖片、其他 JPEG 編碼器或所有 QF10～100 的每個整數。
- 個別新 runner 產生的 G6 marked PNG SHA-256 曾與歷史封存值不同，故不得宣稱所有不同 runner 的影像 bytes 完全相同。新的實驗會記錄 SHA-256 並核對歷史 QF5/10/15 的 32-bit BER checkpoint；跨平台位元完全一致仍須額外驗證。
- 選出的演算法是在首輪三組數據上探索後得到，另外四組是不同 payload 的交叉檢驗，但不代表完全獨立的圖像級驗證。

## 8. 可重現性與檔案

- Pilot-free 候選程式：experiments/g6_no_pilot_32bit_comparison.py
- 冰凍方法獨立驗證：experiments/g6_32bit_independent_holdouts.py
- 初步錯誤定位：experiments/g6_failure_localize_and_pilot.py
- QF1～15 實測：experiments/g6_qf1_to15_diagnostic.py
- CI 工作流程：.github/workflows/g6-qf-low-diagnostic.yml
- 第一輪通過： https://github.com/Rookie-YCLin/matrix-jpeg-research/actions/runs/42561970449
- 第二輪四組新資料通過： https://github.com/Rookie-YCLin/matrix-jpeg-research/actions/runs/42562832733
- 實驗 PR： https://github.com/Rookie-YCLin/matrix-jpeg-research/pull/34

**結論：** 在這張圖與這批 QF／payload 的受控實驗中，維持原本 32-bit G6 嵌入圖、不增加 Pilot，只透過兩個奇異值的交叉極性檢查與軟 QIM 融合，即可顯著降低 QF5～8 BER，並於所有已測 QF≥10 保持零錯誤。仍應將其定位為探索性、樣本限定的改良。