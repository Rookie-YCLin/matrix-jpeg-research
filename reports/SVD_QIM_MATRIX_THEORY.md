# 第一奇異值步長與盲式浮水印的 JPEG 強韌性

## 摘要

本研究以 guofei 的盲式浮水印原版 SVD-QIM 為基準，固定單張上游影像、32 位元訊息及 JPEG 編碼條件，僅將第一奇異值的量化步長 $d_1$ 由 36 改為 90，第二項維持 $d_2=20$。由嵌入與判決公式可知，第一票在理想格點的局部裕度由 9 擴為 22.5。同時，固定奇異向量下的區塊修改量有較寬的 Frobenius 範數上界，提供比較畫質代價的理由。在預先指定的 QF15，正式訊息的擷取錯誤由 32/32 降至 0/32。這是固定條件下的實測結果。矩陣不等式提供局部判決的充分條件，獨立配對量測中，G6 的 QF15 PSNR 低 1.671 dB，嵌入 PNG PSNR 低 6.600 dB，呈現此案例的 BER 與畫質取捨。

## 一、研究問題與比較基準

盲式擷取端由受測影像、訊息長度、金鑰和預定參數取得位元估計，不使用原圖或正確位元。本研究的問題是：在其餘流程一致時，放大第一奇異值的量化步長，能否降低指定 JPEG 攻擊下的位元錯誤率（BER），並伴隨可量化的影像品質差異？

上游固定於 commit `322c90dc02d45644692095b34d3a6b735b6edbd8`。唯一測試圖為上游 `examples/pic/ori_img.jpeg`（高 1108 × 寬 738，Git blob `ef48a056b3cab1d2c08723c014d8d515963f5a07`，SHA-256 `17bed8cfeb5534351d2f35d4addd9407e0c0132132444276a0f826c7ae9923c2`）。正式 payload 是原始 32 bits `10110010111001000101101011010001`，兩把金鑰皆為 1。沿用完整區塊 SVD 路徑（`fast_mode=False`）與原版 DWT、DCT、三色通道、區塊重複嵌入、分群及位元順序還原。每個 JPEG 測試點由各自的含水印 PNG 獨立編碼，使用 Pillow RGB、4:4:4、`subsampling=0`、`optimize=False`、`progressive=False`。嵌入與擷取均採各版本相同的步長。正確位元只用於擷取後計分。[上游核心程式][core] · [公開 bit 介面][bit-api] · [固定實作與驗證][validation] · [輸入與設定 manifest][manifest]

## 二、從區塊 SVD 到原版餘數判決

### 2.1 SVD 與嵌入矩陣

令 $A\in\mathbb R^{4\times4}$ 為某一色彩通道中，同一空間位置的 Haar DWT 近似子頻帶區塊，經 DCT、係數重排及重新整形後所得的矩陣。這是傳入 SVD 的區塊，與整張 RGB 像素矩陣處在不同表示空間。由 SVD，存在正交矩陣 $U,V$ 使

$$
A=U\Sigma V^{\mathsf T},\qquad
\Sigma=\operatorname{diag}(\sigma_1,\sigma_2,\sigma_3,\sigma_4),\qquad
\sigma_1\ge\sigma_2\ge\sigma_3\ge\sigma_4\ge0.
$$

在這個分解中，每個 $\sigma_i$ 乘在秩一方向 $u_iv_i^{\mathsf T}$ 上。原版僅更新前兩個對角值，以原來的 $U,V$ 重建

$$
A'=U\operatorname{diag}(q_1,q_2,\sigma_3,\sigma_4)V^{\mathsf T}.
$$

此處先稱 $q_i$ 為「嵌入後的對角值」。重新 SVD 會將這些非負值按大小排列。只有在更新值與目標索引相容時，才能在擷取端以同一索引讀回 $q_i$。SVD 的存在性與降序定義見 Bernstein 第 2 版 `5.6，印刷頁 301 的 Definition 5.6.1、式 (5.6.2)，以及印刷頁 302–303 的 Theorem 5.6.4、式 (5.6.11)。該定理對非零矩陣表述，零矩陣取零對角即可。

### 2.2 量化格點與局部裕度

原版已有 QIM（量化索引調變）。對第 $i=1,2$ 項，令 $d_i>0$ 為步長，$b\in\{0,1\}$ 為同一區塊嵌入的位元。由原始程式直接寫成

$$
k_i=\left\lfloor\frac{\sigma_i}{d_i}\right\rfloor,\qquad
q_i=d_i\left(k_i+\frac14+\frac b2\right).
$$

當 $b=0$，餘數為 $d_i/4$；當 $b=1$，餘數為 $3d_i/4$。令 $\widehat{\sigma}_i$ 為受測區塊重新 SVD 後的第 $i$ 大奇異值，原版局部票為

$$
h_i=\mathbf 1\!\left[(\widehat{\sigma}_i\bmod d_i)>d_i/2\right].
$$

將模 $d_i$ 餘數想成週期長度為 $d_i$ 的圓周。判決會在 $d_i/2$ 及餘數折返的 0 處切換，兩種理想格點到最近邊界的距離皆為 $m_i=d_i/4$。使用嚴格不等式保證留在原判決區間內，不需額外規定擾動恰好碰到邊界時的結果。

| 版本 | $d_1$ | 第一票理想裕度 $d_1/4$ | $d_2$ | 第二票理想裕度 $d_2/4$ |
|---|---:|---:|---:|---:|
| 原版 | 36 | 9 | 20 | 5 |
| G6 | 90 | 22.5 | 20 | 5 |

放大 $d_1$ 使第一票的理想裕度成為原來的 $22.5/9=2.5$ 倍，且直接作用於局部融合中權重較大的票。原版每個通道區塊先算 $w=(3h_1+h_2)/4$，再將同一訊息位置的分數跨區塊及三通道平均。公開 bit 介面對整串平均分數做一維 K-means，將高分群標為 1，最後依金鑰還原位元順序。若某區塊第一票正確，嵌入 0 時 $w\le1/4$，嵌入 1 時 $w\ge3/4$，不論第二票為何。這解釋第一票的工程重要性。整個 payload 是否正確還取決於有多少區塊保留判決、各訊息位置的平均分數與最後分群。G6 只改步長，沿用原版的 QIM 與擷取規則。[上游實作][core] · [G6 最小 patch][patch]

## 三、JPEG 有效擾動與理想局部充分條件

令 $B$ 為含水印 PNG 解碼後，按相同通道、區塊位置及變換流程所得的區塊矩陣，$B_J$ 為 JPEG 攻擊後的對應矩陣，定義 $E=B_J-B$。$E$ 是兩個區塊在 SVD 輸入域的差。QF15 是編碼器設定，不能代入 $\|E\|_2$。理想重建矩陣 $A'$ 與實際 PNG 區塊 $B$ 也可能不同，例如逆變換、裁切與存檔量化會先引入偏差。

**定理依據。** Bernstein `9.6，印刷頁 562，Proposition 9.6.8 的式 (9.6.19) 對同尺寸矩陣給出奇異值加法上界。取索引 $(i,1)$，應用於 $B+E$，得

$$
\sigma_i(B+E)\le \sigma_i(B)+\sigma_1(E).
$$

再應用於 $B=(B+E)+(-E)$，且 $\sigma_1(-E)=\sigma_1(E)=\|E\|_2$，故

$$
\sigma_i(B)\le\sigma_i(B+E)+\|E\|_2,
\qquad
|\sigma_i(B+E)-\sigma_i(B)|\le\|E\|_2.
$$

這是本報告由該命題寫出的雙向推導，適用於同一降序索引的**數值**，不追蹤同一個奇異向量。式中 $\|E\|_2$ 是譜範數，等於最大奇異值（Bernstein 印刷頁 549，式 (9.2.15)）。

**假設與推論。** 若 $\sigma_i(B)=q_i$，且 $q_i$ 在索引 $i$ 上對應正確步長與位元格點，則 $\|E\|_2<d_i/4$ 足以讓該票維持判決。如果 PNG 起點與理想格點已有偏差 $\eta_i=|\sigma_i(B)-q_i|$，在索引與步長仍相容的前提下，可由三角不等式用 $\eta_i+\|E\|_2<d_i/4$ 作更嚴格的充分條件。實驗未以此條件逐塊驗證 JPEG 攻擊，也不能由界式推出最終 BER。

排序前提可用手算檢查。取 $(\sigma_1,\sigma_2,\sigma_3,\sigma_4)=(80,60,5,1)$、$b=0$，G6 原版格點公式產生 $(22.5,65,5,1)$。理想重分解先讀到 65，以 $d_1=90$ 判決時，$65>45$，第一票反而讀為 1。即使沒有 JPEG 擾動，這個算例也說明「對角值落在格點」本身不足以保證讀回。它只用來展示前提，未主張實際影像存在此區塊，也不代表 G6 使用了保序量化。

## 四、從區塊修改量到整圖 PSNR

### 4.1 固定奇異向量下的區塊失真

令 $\delta_i=q_i-\sigma_i$，$D=\operatorname{diag}(\delta_1,\delta_2,0,0)$。由 $A'-A=UDV^{\mathsf T}$、$U^{\mathsf T}U=V^{\mathsf T}V=I$ 與跡的循環性，

$$
\|A'-A\|_F^2
=\operatorname{tr}(VD^{\mathsf T}U^{\mathsf T}UDV^{\mathsf T})
=\operatorname{tr}(D^{\mathsf T}D)
=\delta_1^2+\delta_2^2.
$$

這個等式不依賴 $D$ 或重建對角值的排序，只需原版重建所用的正交基底保持固定。Frobenius 範數定義見 Bernstein `9.2，印刷頁 547，式 (9.2.5)–(9.2.7)；上述為本報告的直接推導。

令 $f_i=\sigma_i/d_i-\lfloor\sigma_i/d_i\rfloor\in[0,1)$，則 $\delta_i=d_i(1/4+b/2-f_i)$。由此得

$$
\begin{array}{ll}
b=0:& -3d_i/4<\delta_i\le d_i/4,\\
b=1:& -d_i/4<\delta_i\le 3d_i/4.
\end{array}
$$

因此 $|\delta_i|\le3d_i/4$，進而

$$
\|A'-A\|_F\le \tfrac34\sqrt{d_1^2+d_2^2}
=\begin{cases}
\tfrac34\sqrt{1696}\approx 30.89,&(36,20),\\
\tfrac34\sqrt{8500}\approx 69.15,&(90,20).
\end{cases}
$$

這是變換域單一通道區塊的保守上界。步長改變也會改變格點位置，實際修改量未必增加。例如 $b=0$、$\sigma_1=113$ 時，兩組 $d_1$ 分別將 113 改為 117 與 112.5，絕對改動反而由 4 降為 0.5。較大的理想裕度與較寬的最壞修改上界說明為何需要同時量測 BER 與 PSNR。上界本身不決定影像畫質差多少，甚至不決定差異方向。

### 4.2 兩種 PSNR 的像素基準

令 $I$ 為原始 JPEG 檔解碼後的 8-bit RGB 像素，$W$ 為各版本的含水印 PNG 解碼像素，$J_{15}$ 為各自從 $W$ 以 QF15 編碼、再解碼的 RGB 像素。對任何與 $I$ 同尺寸、同通道的比較影像 $X$，以 float64 相減，將 RGB 陣列展開後計算

$$
\operatorname{MSE}(I,X)=\frac{\|I-X\|_F^2}{3HW},\qquad
\operatorname{PSNR}(I,X)=10\log_{10}\!\left(\frac{255^2}{\operatorname{MSE}(I,X)}\right).
$$

MSE 為零時記為 $+\infty$。原圖本來就是 JPEG，因此基準是該檔解碼所得的 RGB，並非未知的壓縮前原始影像。主要畫質比較是 $\operatorname{PSNR}(I,J_{15})$，它包含嵌入與攻擊的總差異；輔助比較 $\operatorname{PSNR}(I,W)$ 描述嵌入後、攻擊前的畫質。逆 DCT、逆 DWT、色彩轉換、裁切、存檔與 JPEG 量化介於兩種表示空間之間，不能用區塊上界直接換算整圖 PSNR。

配對差值一律取「G6 減原版」，且只比較相同階段。若兩組 MSE 均為正，$\Delta\operatorname{PSNR}=10\log_{10}(\operatorname{MSE}_{\mathrm{base}}/\operatorname{MSE}_{\mathrm{G6}})$。同一版本的前後 PSNR 差也不能解讀為獨立的 JPEG 失真，因為 $I-J_{15}=(I-W)+(W-J_{15})$，平方和含兩項誤差的內積交叉項。

### 4.3 QF15 配對畫質實測

下表由獨立量測 PR #29 的固定 CSV 取值。兩個階段均以同一原始 JPEG 解碼的 RGB 像素為基準。差值由全精度數值計算，再顯示至小數三位。

| 階段 | 原版 MSE | G6 MSE | 原版 PSNR | G6 PSNR | G6 − 原版 |
|---|---:|---:|---:|---:|---:|
| 嵌入 PNG | 9.396396 | 42.950692 | 38.401 dB | 31.801 dB | −6.600 dB |
| QF15 JPEG 解碼 | 77.730415 | 114.211263 | 29.225 dB | 27.554 dB | −1.671 dB |

在 QF15，原版 32/32 錯、G6 0/32 錯，伴隨最終影像 PSNR 下降 1.671 dB。攻擊前的兩張 PNG 都能正確擷取，但 G6 的嵌入 PSNR 低 6.600 dB。兩個差值各自對應同階段的版本比較。此次量測的 PNG 檔案雜湊與歷史存檔不同，PSNR 使用本次重生的 PNG；兩組 QF15 JPEG 的 SHA-256 與擷取位元則各自重現歷史紀錄。兩次本機重跑的六個索引檔案 SHA-256 一致。[PSNR CSV][psnr-csv] · [量測 manifest][psnr-manifest] · [量測 PR #29][psnr-pr] · [量測 CI][psnr-ci]

## 五、已驗證 BER 與研究限制

原版先以 QF5–95 每 5 一點掃描。QF15、QF20 並列最大 BER，依預定規則取較小者 QF15。其後曾比較 15 組有限候選，選擇 $(90,20)$ 作只變一個步長的方案，再重驗完整品質網格與兩組未參與選擇的 32 位元訊息。這兩組提供同圖上的額外訊息檢查，仍未構成跨圖驗證。

| 品質條件 | 原版錯誤數 / 32 | G6 錯誤數 / 32 |
|---|---:|---:|
| QF5 | 12 | 32 |
| QF10 | 1 | 0 |
| **QF15（主條件）** | **32** | **0** |
| QF20 | 32 | 0 |
| QF25、30、…、95（每 5） | 各 0 | 各 0 |

在主條件，原版 BER 為 100%，G6 為 0%，相對降幅 $(1-0)/1\times100\%=100\%$，達到預定 10% 優秀門檻。兩組追加訊息在 QF15 也各由 32/32 降至 0/32，三組訊息的兩個版本在無攻擊 PNG 皆為 0/32。原版主訊息在 QF15、QF20 的輸出與正確訊息逐位互補。這是輸出現象，現有證據未判定是何種機制所致。QF5 的退步保留為限制。零觀察錯誤限於實際測點、固定圖片、設定與所試位元序列，不外推至所有整數 QF、其他影像或普遍零 BER。理論沒有選出 $d_1=90$，有限比較也未證明其為最優值。[原版選點 CSV][baseline] · [逐位 CSV][results] · [manifest][manifest] · [候選紀錄][sweep] · [G6 驗證 CI][ci]

## 六、結論

原版第一票在融合中權重較大。調大其步長可加寬理想局部判決裕度，也會放寬變換域區塊的最壞修改上界。這是單參數比較的數學動機。固定條件下的 QF15 實測支持所選方案可降低 BER。局部擾動界不解釋整體分群結果，在相同 RGB 基準下，實測的最終 QF15 影像 PSNR 低 1.671 dB，顯示這次 BER 改善伴隨可量化的像素畫質代價。

## 來源與重現

- Dennis S. Bernstein, *Matrix Mathematics: Theory, Facts, and Formulas*, 2nd ed., Princeton University Press, 2009。已核對書中印刷頁 301–303、547、549、562。該書提供矩陣定理與範數依據，QIM、JPEG 及 BER 的內容各由上游程式與本研究實測支持。
- Guofei, `blind_watermark` 固定提交。[核心程式][core] · [bit 介面][bit-api] · [MIT 授權][license]。
- 在證據提交以 Python 3.13 安裝該提交的 Research CI 所用依賴與固定上游，於新目錄執行 `python -m experiments.svd_qim_validation --output-dir <new-empty-dir>`。核對輸入雜湊、位元輸出及 manifest。命令用於重現既有 G6 驗證，本報告使用封存資料。[Research CI 配置][workflow] · [驗證腳本][validation]

[core]: https://github.com/guofei9987/blind_watermark/blob/322c90dc02d45644692095b34d3a6b735b6edbd8/blind_watermark/bwm_core.py
[bit-api]: https://github.com/guofei9987/blind_watermark/blob/322c90dc02d45644692095b34d3a6b735b6edbd8/blind_watermark/blind_watermark.py
[license]: https://github.com/guofei9987/blind_watermark/blob/322c90dc02d45644692095b34d3a6b735b6edbd8/LICENSE
[patch]: ../patches/bwm_core_svd_d1_90.patch
[validation]: ../experiments/svd_qim_validation.py
[manifest]: ../outputs/svd-qim-qf15-selected/manifest.json
[results]: ../outputs/svd-qim-qf15-selected/results.csv
[sweep]: ../outputs/svd-qim-qf15-exploration/results.csv
[workflow]: ../.github/workflows/research-ci.yml
[ci]: https://github.com/Rookie-YCLin/matrix-jpeg-research/actions/runs/42463429539

- PSNR 以獨立 PR #29 的固定提交 `2f444b7028cb61241e98dec1103ef5b5b7ac9b9e` 重現，按其安裝指令，在兩個新目錄執行 `python -m experiments.svd_qim_psnr --output-dir <new-empty-dir>`，再比較 manifest 及輸出雜湊。[量測與重跑說明][psnr-report]

[baseline]: ../outputs/ori-qf-scan/results.csv
[psnr-pr]: https://github.com/Rookie-YCLin/matrix-jpeg-research/pull/29
[psnr-csv]: https://github.com/Rookie-YCLin/matrix-jpeg-research/blob/2f444b7028cb61241e98dec1103ef5b5b7ac9b9e/outputs/svd-qim-psnr-qf15/results.csv
[psnr-manifest]: https://github.com/Rookie-YCLin/matrix-jpeg-research/blob/2f444b7028cb61241e98dec1103ef5b5b7ac9b9e/outputs/svd-qim-psnr-qf15/manifest.json
[psnr-report]: https://github.com/Rookie-YCLin/matrix-jpeg-research/blob/2f444b7028cb61241e98dec1103ef5b5b7ac9b9e/reports/SVD_QIM_PSNR_TRADEOFF.md
[psnr-ci]: https://github.com/Rookie-YCLin/matrix-jpeg-research/actions/runs/42476284890
