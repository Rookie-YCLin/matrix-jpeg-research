# SVD-QIM 量化步長對 JPEG 浮水印強韌性與影像品質之影響

> 2026-11-08 G6 正式整合報告。舊版 [FINAL_REPORT.md](FINAL_REPORT.md) 屬早期不同題目的 JPEG 低秩研究，保留作歷史資料。本報告封面、作者、學號、教師、課程格式尚待依繳交規定填寫。

## 摘要

本研究以 guofei9987/blind_watermark 原版盲式 SVD-QIM 為基礎，固定一張上游血小板圖片、32-bit payload、兩把密鑰及 JPEG 4:4:4 編碼條件，僅將第一奇異值量化步長由 $d_1=36$ 調整為 $90$，第二步長維持 $d_2=20$。在事前指定的 JPEG QF15，原版 32/32 位錯誤（BER 100%），改良 G6 0/32（BER 0%）；但攻擊後 PSNR 由 29.225 dB 降至 27.554 dB（差 −1.671 dB），嵌入後未受 JPEG 攻擊的 PNG 則降低 6.600 dB。本報告以 SVD、QIM 判決裕度、奇異值擾動不等式及 Frobenius 範數建立數學動機，分別處理理論的局部充分條件與全系統的實測證據。結果顯示固定案例中，盲式擷取可靠性與影像品質有工程取捨；並不代表所有品質因子或影像均改善。

**關鍵字**：奇異值分解、QIM、JPEG、盲式浮水印、BER、PSNR、Frobenius 範數、Trade-off。

## 一、研究動機與實際貢獻

影像在 JPEG 壓縮後可能影響 SVD-QIM 位元擷取。研究問題是：**在只改第一奇異值量化步長的條件下，能否降低指定 JPEG QF15 的 BER？因此付出多少影像品質代價？**

原版已具有 DWT、DCT、SVD、QIM、跨區塊融合與 K-means；**本研究沒有發明這些方法**。貢獻是固定可重現的 BER–QF 基準、有限候選中採用單參數 G6 方案、配對 PSNR、以及用矩陣理論解釋其合理性和限制。

原版先掃描 QF=5,10,…,95；QF15 和 QF20 都達到最高原版 BER 32/32，依預先約定的並列取較小 QF 規則固定 **QF15** 為主條件。選用 $(90,20)$ 之前已測過 15 組有限候選；**不能宣稱是全域最優，也不能宣稱完全由定理預測出 90**。

## 二、可重現實驗條件

| 項目 | 固定設定 |
|---|---|
| 上游 | guofei9987/blind_watermark commit 322c90dc02d45644692095b34d3a6b735b6edbd8 |
| 唯一圖檔 | examples/pic/ori_img.jpeg；解碼後 RGB，高 1108、寬 738 |
| 圖檔 SHA-256 | 17bed8cfeb5534351d2f35d4addd9407e0c0132132444276a0f826c7ae9923c2 |
| 32-bit payload | 10110010111001000101101011010001 |
| image／watermark 金鑰 | 均為 1 |
| SVD | 原版完整區塊流程，fast_mode=False |
| 比較組 | 原版 $(36,20)$ 與改良 G6 $(90,20)$，嵌入及擷取同步更動 |
| JPEG | Pillow QF15、RGB、4:4:4，subsampling=0、optimize=False、progressive=False |
| 評分 | 真實 payload 僅供盲式擷取完成後計算 BER |

各組由同一來源產生各自嵌入 PNG，再各自 JPEG 編碼／解碼；不能使用正確位元當解碼端輸入。歷史驗證及最新實測資料可由 [BER CSV](../outputs/svd-qim-qf15-selected/results.csv) 和 [PSNR CSV](../outputs/svd-qim-psnr-qf15/results.csv) 追溯。

## 三、矩陣理論：從 SVD、QIM 到擾動界

### 3.1 變換域區塊的 SVD

令 $A\in\mathbb R^{4\times4}$ 為送入原版區塊 SVD 的變換域矩陣，而不是整張 RGB 像素矩陣。Bernstein 的 SVD 定理保證

$$
A=U\Sigma V^\mathsf T,\qquad U^\mathsf TU=V^\mathsf TV=I,\qquad
\sigma_1\ge\sigma_2\ge\sigma_3\ge\sigma_4\ge0.
$$

原版量化前兩項並使用相同奇異向量重建：

$$ A'=U\operatorname{diag}(q_1,q_2,\sigma_3,\sigma_4)V^\mathsf T.$$

重新 SVD 時奇異值會重新排序，因此量化後 $q_1,q_2$ 是否仍為第一、第二大奇異值，是局部判決的重要前提。

### 3.2 QIM 量化格點與判決裕度

原版已有以下嵌入公式，並非 G6 新發明：

$$
q_i=d_i\left(\left\lfloor\frac{\sigma_i}{d_i}\right\rfloor+\frac14+\frac b2\right),\quad
b\in\{0,1\},\quad i=1,2.
$$

原版局部擷取票為 $h_i=\mathbf1[(\widehat\sigma_i\bmod d_i)>d_i/2]$。理想餘數格點為 $d_i/4$（位元 0）及 $3d_i/4$（位元 1），在週期性 modulo 判決中距最近邊界 $0$ 或 $d_i/2$ 都是 $d_i/4$，因此

$$m_i=d_i/4,\qquad m_1:9\longrightarrow22.5\;(2.5\text{ 倍}).$$

原版區塊融合採 $(3h_1+h_2)/4$，第一票佔 3/4 權重，但**不能**把此權重直接解釋成第一奇異值決定 75% BER。後續仍有多區塊、三通道平均及 K-means。

### 3.3 奇異值擾動界的正反向推導

定義同一變換域、對應區塊的實際嵌入後矩陣 $B$、JPEG 後矩陣 $B_J=B+E$，$E$ 是兩者的有效擾動。JPEG 的 QF 數字並非 $\|E\|_2$。

由 Bernstein Proposition 9.6.8 的奇異值加法上界：

$$\sigma_i(B+E)\le\sigma_i(B)+\sigma_1(E).$$

再將 $B=(B+E)+(-E)$ 套入同一不等式，利用 $\sigma_1(-E)=\sigma_1(E)=\|E\|_2$，得到

$$
\boxed{|\sigma_i(B+E)-\sigma_i(B)|\le\|E\|_2.}
$$

這個界約束按大小排序的奇異值**數值**，並非持續追蹤同一奇異向量。**只有當** $\sigma_i(B)$ 落在對應的理想 $q_i$、奇異值索引相容時，$\|E\|_2<d_i/4$ 才是該局部票不跨界的充分條件。如果 PNG 起點偏差 $\eta_i=|\sigma_i(B)-q_i|$，則可採更保守的 $\eta_i+\|E\|_2<d_i/4$。本實驗**沒有逐區塊證明** JPEG 滿足該條件，不能因此推導最終 BER=0。

反例：原本對角值 $(80,60,5,1)$，嵌入 $b=0$，在 G6 $(90,20)$ 下前兩項量化成 $(22.5,65)$。重新 SVD 依序為 $(65,22.5,5,1)$，用 $d_1=90$ 判第一票會讀到錯誤位元。這是理論適用前提的反例，不是聲稱實驗圖片一定出現此區塊。

### 3.4 Frobenius 範數與修改量上界

令 $\delta_i=q_i-\sigma_i$，固定正交矩陣重建給出

$$\boxed{\|A'-A\|_F^2=\delta_1^2+\delta_2^2.}$$

令 $f_i=\sigma_i/d_i-\lfloor\sigma_i/d_i\rfloor\in[0,1)$，代入量化公式得 $\delta_i=d_i(1/4+b/2-f_i)$，故 $|\delta_i|\le3d_i/4$。因此

$$
\|A'-A\|_F\le\frac34\sqrt{d_1^2+d_2^2}.
$$

原版上界約 30.89，G6 約 69.15。**這只是變換域單一區塊的保守上界，不是實際修改量，也不是 PSNR 值**。步長放大不能保證每個區塊的實際失真單調增加；影像從變換域經逆 DCT／逆 DWT、裁切、量化及 JPEG 編解碼，必須額外量測 RGB PSNR。

上述引用 Bernstein, *Matrix Mathematics: Theory, Facts, and Formulas*, 2nd ed. (2009)，§5.6 pp.301–303（Definition 5.6.1、Theorem 5.6.4）、§9.2 pp.547、549（Frobenius 與譜範數）、§9.6 p.562（Proposition 9.6.8）。**QIM 及對其套用的局部分析屬本研究依上游程式推導**，Bernstein 沒有直接研究此浮水印程式或 JPEG。

## 四、BER、MSE 與 PSNR 實測

定義 $\mathrm{BER}=\text{錯誤位元數}/32$。對原始 JPEG 解碼後的 8-bit RGB 像素 $I$，與同尺寸結果 $X$：

$$
\mathrm{MSE}(I,X)=\frac{\|I-X\|_F^2}{3HW},\qquad
\mathrm{PSNR}(I,X)=10\log_{10}\frac{255^2}{\mathrm{MSE}(I,X)}.
$$

RGB 差值以 float64 計算，避免 uint8 溢位；MSE=0 時 PSNR=$+\infty$。原圖**本身為 JPEG**，基準是它的解碼 RGB，而非未知的壓縮前來源。

| 對照階段 | 原版 MSE | G6 MSE | 原版 PSNR | G6 PSNR | ΔPSNR（G6−原版） |
|---|---:|---:|---:|---:|---:|
| 嵌入 PNG、未受攻擊 | 9.396396 | 42.950692 | 38.401 dB | 31.801 dB | **−6.600 dB** |
| JPEG QF15 攻擊後 | 77.730415 | 114.211263 | 29.225 dB | 27.554 dB | **−1.671 dB** |

每列兩組均相對同一原圖 RGB。第一列反映嵌入後像素差異；第二列反映嵌入與 JPEG 攻擊的**總**差異。兩列 PSNR 不能相減當成獨立的 JPEG 失真，因為平方差含交叉項。兩張 QF15 JPEG 的雜湊與歷史封存一致；這次 PNG 的**檔案**雜湊與歷史不同，已於 [PSNR 詳細報告](SVD_QIM_PSNR_TRADEOFF.md) 說明。已有 21 項 pytest 通過以及固定 QF15 CI 重跑。

| 既定 JPEG QF | 原版錯誤／32 | G6 錯誤／32 |
|---|---:|---:|
| 5 | 12 | **32（退步）** |
| 10 | 1 | 0 |
| **15（正式主條件）** | **32** | **0** |
| 20 | 32 | 0 |
| 25,30,…,95（每 5 點） | 各 0 | 各 0 |

QF15 相對 BER 降幅 100%；但原版 QF15、20 的輸出正好與真值逐位互補，原因**尚未確認**，不能直接歸咎 K-means 分群極性。兩組獨立選參數後追加的 32-bit payload 也在**同圖** QF15 由 32/32 改至 0/32，不能當成跨圖驗證。

## 五、討論與結論：可量化的 Trade-off

在固定圖片、payload、金鑰、JPEG QF15 條件下，改良 G6 的 BER 由 100% 降至 0%，但最終 PSNR 下降 1.671 dB，嵌入 PNG PSNR 下降 6.600 dB。**這是本次可靠性改善伴隨影像品質代價的實驗證據**。理論上的 $d_1/4$ 局部裕度與 Frobenius 範數上界解釋為何值得檢驗這個工程取捨，但不精確預測實際 BER 或 PSNR。

本研究沒有做多圖片普遍性檢驗、所有整數 QF、人體主觀可見度、$d_1$ 全域最優證明，也未逐塊驗證 JPEG 擾動上界。QF5 退步必須揭露；QF15 原版完整反相的機制尚未證實。成功主張僅限**已實測條件**。

## 六、來源、再現及答辯

1. Dennis S. Bernstein, *Matrix Mathematics: Theory, Facts, and Formulas*, 2nd ed., Princeton University Press, 2009，§5.6、§9.2、§9.6（僅引用定理與範數，原書 PDF 不上傳公共倉庫）。
2. [guofei9987/blind_watermark 固定版本](https://github.com/guofei9987/blind_watermark/tree/322c90dc02d45644692095b34d3a6b735b6edbd8)；[最小 d1 修改 patch](../patches/bwm_core_svd_d1_90.patch)。
3. [G6 完整 BER 報告](G6_SVD_QIM_QF15_SUCCESS.md) · [BER CSV](../outputs/svd-qim-qf15-selected/results.csv) · [BER 重現腳本](../experiments/svd_qim_validation.py) · [原始驗證 CI](https://github.com/Rookie-YCLin/matrix-jpeg-research/actions/runs/42463429539)。
4. [PSNR 詳細報告](SVD_QIM_PSNR_TRADEOFF.md) · [PSNR CSV](../outputs/svd-qim-psnr-qf15/results.csv) · [PSNR 重現腳本](../experiments/svd_qim_psnr.py) · [固定 QF15 CI](https://github.com/Rookie-YCLin/matrix-jpeg-research/actions/runs/42476284890)。
5. [更完整的數學推導與排序反例](SVD_QIM_MATRIX_THEORY.md) · [90 秒答辯與七問](SVD_QIM_DEFENSE_BRIEF.md)。

依 [PSNR 詳細報告](SVD_QIM_PSNR_TRADEOFF.md) 安裝固定環境後，在新目錄執行 python -m experiments.svd_qim_psnr --output-dir outputs/reproduce-psnr。BER 的 19 點掃描可由 python -m experiments.svd_qim_validation --output-dir outputs/reproduce-ber 重現。輸出目錄須事前不存在，不覆蓋封存的 CSV 或 manifest。
