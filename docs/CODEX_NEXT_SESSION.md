# Codex 交接｜新原圖與 QF=x 優先

## 最新：QF15 SVD 改良達標，停止候選搜尋

- 上游第一奇異值 QIM 步長 d1=36→90；固定 x=QF15 原版32/32錯→G6 0/32，BER相對降低100%；其餘原版步驟固定。
- 已跑完整19點 QF 及兩組額外 payload。**QF5 會退步（12/32→32/32）**，這是正式結果適用範圍的限制，不可被忽略。
- [成果報告](../reports/G6_SVD_QIM_QF15_SUCCESS.md) · [驗證CSV](../outputs/svd-qim-qf15-selected/results.csv) · [上游 patch](../patches/bwm_core_svd_d1_90.patch)。根據主持人規格，成功後不再開新的候選搜尋，改進報告及可重現性查核。


**倉庫管理授權（2026-11-08）**：研究主持人已授權專題倉庫全權管理；代理可自行建立、修訂、刪除適當檔案、開啟與合併 PR、更新 `main`、執行既定實驗及管理分支，**不需要逐項徵求批准**。保留可重現證據、上游授權及真實研究紀錄；重大研究判斷自主決策並在互動中主動回報。

**主持人已核定（2026-11-08）**：完整掃描 **QF=5、10、15、…、95（19 點）**；原版 BER 最大值若有多個 QF 並列，**取其中最小 QF**，將該值固定為 `x`，再測試 SVD 候選。相對 BER 降幅 `R=(BER_base(x)-BER_new(x))/BER_base(x)×100%`，**R≥5% 達標，R≥10% 優秀**。這些已非待決設定。


## 最新一次交接：唯一來源與 QF=x（2026-11-08）

- 測試原圖改為 [上游指定測試圖](https://github.com/guofei9987/blind_watermark/blob/master/examples/pic/ori_img.jpeg)（blob SHA `ef48a056b3cab1d2c08723c014d8d515963f5a07`），**一張即可**。舊三圖 W0–G5 測試值僅為歷史，不可直接當新原圖的 baseline。
- 下一步先凍結 QF 掃描範圍（已核准 5–95、step 5）與最大值並列的處理規則；用原版在全部 QF 計算 BER，`x` 取原版 BER 最高的 QF。
- 對改良 SVD 只比較相同 QF=x 的 BER。主持人已確認 **A：相對降幅** `R=(BER_base-BER_new)/BER_base×100%`；**R ≥ 5% 達標、R ≥ 10% 優秀**，不以百分點為判準。列出原始錯誤數、分母、BER 與 R；基準 BER=0 時先處理不可計算情況。
- 新原圖尚未執行正式實驗，也尚未知 x。每輪需回報；不得擅自當作已有正向結果。


## 唯一正式目標
以 [guofei9987/blind_watermark](https://github.com/guofei9987/blind_watermark) 為基礎，修改 [bwm_core.py](https://github.com/guofei9987/blind_watermark/blob/master/blind_watermark/bwm_core.py) 內 SVD 嵌入或擷取演算法，降低**低 JPEG QF** 的 BER。上游 [att.py](https://github.com/guofei9987/blind_watermark/blob/master/blind_watermark/att.py) 未涵蓋本專題所需 JPEG 攻擊，須採用本倉庫可重現的 JPEG 編解碼測試。

## 工作流程
1. 先用固定 SHA 原版建立不同 QF 的 BER 基準（已有 W0／W0-D 存檔）。
2. 提出一項有矩陣理論動機的 SVD 局部改良，事前固定比較條件；跟原版配對比較各 QF 的 BER。原版及改良版都要經過正確的 JPEG 實際編解碼與公開 bit 擷取。
3. 如未改善，記錄結果並提出下一方案；如在預先固定低 QF 下得到可重現的 BER 降低，停止候選搜尋，整理成功方法給報告。

## 目前已有證據
- W0 [#13](https://github.com/Rookie-YCLin/matrix-jpeg-research/pull/13)、W0-D [#14](https://github.com/Rookie-YCLin/matrix-jpeg-research/pull/14)：4:4:4 QF10=12／96、QF20=78／96、QF30=0／96。
- G2 [#17](https://github.com/Rookie-YCLin/matrix-jpeg-research/pull/17)、G3 [#18](https://github.com/Rookie-YCLin/matrix-jpeg-research/pull/18)、G4 [#20](https://github.com/Rookie-YCLin/matrix-jpeg-research/pull/20)、G5 [#21](https://github.com/Rookie-YCLin/matrix-jpeg-research/pull/21)／[#22](https://github.com/Rookie-YCLin/matrix-jpeg-research/pull/22) 是已封存探索；截至目前**沒有確認的低 QF BER 正向成果**。
- 舊「禁止再產生候選」限制已被新的三步驟工作規格取代，但新實驗須先固定假說與比較條件、記錄全數結果，避免無限制事後調參。
- 正式交付只需要來源、JPEG 測試、BER–QF 比較與成功方法的矩陣理論說明，**無須 PSNR、無須逐一記載失敗候選**；內部紀錄仍保留實驗全貌。

## 行動與回報
自行決定及執行正式新實驗，事先固定低 QF 主條件、候選方法、修改範圍及預期驗證方式；完成後主動回報。每階段都更新 GitHub PR／PROGRESS，提供 BER–QF 表格、固定輸出連結、阻礙與明確待決問題。PR 可由倉庫管理者自行合併 main；精簡時保留或歸檔可重現證據。
