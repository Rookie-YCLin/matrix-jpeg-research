# M3 分析草稿｜JPEG 壓縮後的奇異值、低秩近似與原始秩一方向

## 研究問題與實驗基準

同一張灰階影像經 JPEG 壓縮後，像素失真、影像自身的可低秩近似程度，以及沿原始秩一方向的投影如何改變？令 $A$ 為原始 `ascent` 影像矩陣，$B_Q$ 為同一份 $A$ 以品質因子 $Q$ 獨立編碼後的實際解碼矩陣。矩陣大小為 $512\times512$，比較 $Q=40,60,80,95$。輸入雜湊、尺寸、編碼設定與版本見 [M2 manifest](../outputs/run-m2/manifest.json)。所有數值取自 M2 存檔，表格僅做顯示精度的四捨五入。

JPEG 對局部 $8\times8$ 區塊做 DCT，量化後的係數經解碼與反轉換形成像素。這項研究對整幅像素矩陣做 SVD，基底由該影像決定。局部 DCT 頻率與全域奇異值索引描述不同結構。展示用 Rank-k PNG 是將浮點截斷重建裁切、取整後存成無損 PNG。JPEG 的檔案大小則取自實際 JPEG 檔。

## 為何截斷 SVD 是最佳低秩近似

對任一實矩陣 $X\in\mathbb R^{m\times n}$，令 $p=\min(m,n)$，精簡 SVD 為 $X=\sum_{i=1}^p s_i a_i b_i^{\mathsf T}$，其中 $s_1\ge\cdots\ge s_p\ge0$。令 $D_i=a_i b_i^{\mathsf T}$。左右奇異向量各自正交歸一，因此 $\langle D_i,D_j\rangle_F=(a_i^{\mathsf T}a_j)(b_i^{\mathsf T}b_j)=\delta_{ij}$。有正權重的項 $s_iD_i$ 秩為一。保留前 $k$ 項得到秩至多 $k$ 的 $X_k$，且由正交性直接得到 $\|X-X_k\|_F^2=\sum_{i>k}s_i^2$。

要說明這個誤差確實最小，任取秩至多 $k$ 的矩陣 $Y$，令 $P$ 為投影到 $Y$ 欄空間的正交投影。因為 $PY=Y$，正交分解給出
$$
\|X-Y\|_F^2=\|(I-P)X\|_F^2+\|PX-Y\|_F^2
\ge \|X\|_F^2-\|PX\|_F^2.
$$
右奇異向量的正交性給出 $\|PX\|_F^2=\sum_i s_i^2 w_i$，其中 $w_i=\|Pa_i\|^2$ 介於 0 與 1，且 $\sum_i w_i\le\operatorname{rank}(P)\le k$（把 $a_i$ 補成完整正交基即可）。因權重上限為 1、總額至多 $k$，將權重優先給最大的 $s_i^2$ 得上界 $\sum_{i\le k}s_i^2$。因此任何 $Y$ 的誤差至少為尾端平方和，而 $X_k$ 達到此下界。此結論適用於整數 $0\le k\le p$。截斷點若切過相等的正奇異值，最優近似可能不唯一。

當 $\|X\|_F>0$，累積平方能量 $E_k=\sum_{i\le k}s_i^2/\sum_i s_i^2$，自身相對平方誤差 $R_k=\|X-X_k\|_F^2/\|X\|_F^2=1-E_k$。兩者使用同一張圖自己的總平方能量。數值核對使用 float64，依各矩陣對照 [rank_errors.csv](../outputs/run-m2/rank_errors.csv) 的 `frobenius_squared`、`tail_squared` 及其正規化欄位。

## 四組 JPEG 的觀察與解讀

$\operatorname{MSE}(A,B_Q)=\|A-B_Q\|_F^2/(mn)$。8 位元灰階在 MSE 大於零時採用 $\operatorname{PSNR}=10\log_{10}(255^2/\operatorname{MSE})$，MSE 為零時 PSNR 為無限大。這兩個指標以 $A$ 為基準。$R_k(B_Q)$ 衡量 $B_Q$ 相對自身最佳近似的誤差。

| $Q$ | JPEG 檔案大小（bytes） | MSE | PSNR（dB） | $R_{100}(B_Q)$ |
| ---: | ---: | ---: | ---: | ---: |
| 40 | 23,780 | 37.09696 | 32.43742 | 0.46522% |
| 60 | 30,965 | 23.62286 | 34.39748 | 0.52460% |
| 80 | 45,222 | 10.26691 | 38.01641 | 0.53177% |
| 95 | 89,876 | 1.62239 | 46.02924 | 0.52482% |

前三個量測欄取自 [jpeg_metrics.csv](../outputs/run-m2/jpeg_metrics.csv) 各 `quality_factor` 的 `jpeg_bytes`、`mse`、`psnr_db`。末欄取自 [rank_errors.csv](../outputs/run-m2/rank_errors.csv) 各 `image=jpeg_q<Q>`、`k=100` 的 `relative_squared` 乘 100。原圖同欄 `image=original` 為 0.51677%。

- [檔案大小與 PSNR](../outputs/run-m2/jpeg_metrics.png) 的橫軸是實測 bytes，Q 是標註。這四組設定下，Q 越高，檔案越大、PSNR 越高。較高品質通常使用較細的量化，可能減少解碼像素誤差。本實驗的四組觀察不足以建立一般單調定律。
- [低秩誤差](../outputs/run-m2/rank_errors.png) 顯示每張圖的 $R_k$ 隨 $k$ 增大而下降。固定 $k=100$ 改變 Q，$R_k$ 並不單調。Q=40 自身誤差最低，同時相對原圖的 PSNR 也最低。量化可能減弱部分局部細節，使平方能量更集中於少數全域成分。這是與觀察相容的解釋，本實驗未逐一辨識 DCT 係數對全域譜的因果貢獻。
- [頻譜與累積平方能量](../outputs/run-m2/spectra.png) 顯示各圖譜的前段接近，尾段差異較明顯。例如 `i=400` 的 `sigma` 由原圖的 27.10575 變為 Q=40 的 6.09311，Q=95 則為 28.75731。因此不能概括為所有奇異值都縮小。原圖及 Q=40 的前 100 項能量分別為 99.48323% 與 99.53478%，與各自的 $1-R_{100}$ 一致。來源為 [spectrum.csv](../outputs/run-m2/spectrum.csv) 中 `image=original/jpeg_q40/jpeg_q95` 的 `i=400, sigma`，以及 `image=original/jpeg_q40` 的 `i=100, cumulative_energy`。
- [重建拼圖](../outputs/run-m2/reconstructions.png) 中，隨 $k$ 提高，樓梯與欄杆的輪廓逐漸清楚。拼圖最後一格是 Q=80 解碼影像，其餘標示 Rank 的格子是原圖截斷重建。用 [rank_errors.csv](../outputs/run-m2/rank_errors.csv) 的 `image=original`、各 `k` 的 `relative_squared` 核對浮點誤差，視覺展示用 PNG 的裁切與取整不參與此誤差。

## 固定原圖秩一方向的投影

令 $A$ 的奇異向量與奇異值為 $u_i,v_i,\sigma_i$。因 $u_iv_i^{\mathsf T}$ 的 Frobenius 範數為 1，
$$
c_i(Q)=\langle B_Q,u_i v_i^{\mathsf T}\rangle_F=u_i^{\mathsf T}B_Q v_i,\qquad
\Delta_i(Q)=\langle B_Q-A,u_i v_i^{\mathsf T}\rangle_F.
$$
代入 $B_Q=A$ 得 $c_i=\sigma_i$。四組 Q 都使用原圖同一組方向，$c_i$ 帶正負號；$B_Q$ 的奇異值則由其自身 SVD 得到，非負且重新排序。固定方向只取原圖基底中配對的 $i,i$ 項，未涵蓋跨方向成分。這些係數不宜作為資訊保留率。若原圖有重複奇異值，對應子空間可選不同正交基底，單一方向的 $c_i$ 會依基底而變。

[投影圖](../outputs/run-m2/projections.png) 上半部比較有號係數與原圖奇異值，下半部展示差值。以 `i=200` 為例，Q=40 的 $\Delta_i=-75.10047$，Q=95 為 $-1.43469$。Q=95 在 `i=512` 的 $c_i=-1.35063$，而原圖同方向 $\sigma_i=0.15024$，可具體說明投影係數為何能帶負號。來源為 [projections.csv](../outputs/run-m2/projections.csv) 的 `quality_factor=40/95, i=200, delta` 及 `quality_factor=95, i=512, coefficient/original_sigma`。

## 結論草稿與限制

截斷 SVD 提供可以由尾端平方和直接檢查的最佳低秩近似。本個案中，較高 Q 對應較高 PSNR，但 JPEG 相對原圖的像素失真與解碼圖自身的低秩結構可呈現不同趨勢。固定原始方向的有號投影可指出個別成分權重如何改變，與重新分解後的奇異值曲線互補。結論限於單張灰階 `ascent` 與本次編解碼設定。平方能量、PSNR 和有號係數均未直接量測人眼感知、語意資訊或浮水印的存活。

## 題目與研究範圍待確認

原先口頭題目為「SVD 數位浮水印的 JPEG 壓縮分析」。已核准的 [PROJECT_SPEC.md](../PROJECT_SPEC.md) 排除浮水印實作，現有結果涵蓋 JPEG 對奇異值、低秩結構與秩一方向的影響。

- **A｜採用目前 JPEG／SVD 題目。** 與教師確認改用「JPEG 壓縮對影像奇異值、低秩結構與原始秩一方向的影響」，以現有實驗作為正式報告的證據。
- **B｜教師要求保留浮水印時，先另案批准。** 最小延伸可限定同一圖、一個固定嵌入設定與短位元序列、一組無 JPEG 對照及一次 Q=80 壓縮，驗收嵌入影像的 PSNR 與取回位元錯誤率。暫估需額外 1–2 天，取決於是否已有可用嵌入／取回方法。若對照本身無法可靠取回，JPEG 實驗便無法解讀。先提交規格與工時供使用者批准，再決定是否另做，M4 仍以現有結果按原排程交付。

## 口頭答辯準備

1. **為何 Rank-k 是最佳近似？** 任一秩至多 $k$ 的候選只使用最多 $k$ 維欄空間。該空間最多取得前 $k$ 個奇異值的平方和，截斷 SVD 達到此上限，因此殘差平方最小。
2. **為何 Q=40 的自身低秩誤差反而較小？** 在這張圖上，Q=40 的前 100 項占自身平方能量的比例較高。量化後細節可能較弱，所以解碼圖較容易用少量成分近似。其較低 PSNR 同時表明它離原圖更遠。
3. **$c_i$ 與奇異值有何不同？** $c_i$ 沿原圖固定的一對奇異向量量測 $B_Q$，可為負。奇異值沿 $B_Q$ 自身的奇異向量取得，皆非負。
4. **為何 PSNR 與自身 Rank-k 誤差不能直接比較？** PSNR 比較 $A$ 和 $B_Q$ 的像素，使用 dB。自身 Rank-k 誤差比較 $B_Q$ 與其截斷重建，並除以 $B_Q$ 的總平方能量。它們回答的是兩個問題。
