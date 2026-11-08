# Codex 交接｜BER 優先，不自行開新候選

## 研究目標

以 [guofei9987/blind_watermark](https://github.com/guofei9987/blind_watermark) 固定提交 `322c90dc02d45644692095b34d3a6b735b6edbd8` 為基礎，**改良 SVD 區塊的嵌入或擷取演算法，使 JPEG 壓縮後浮水印 BER 低於原版**。不得把 PNG PSNR、SVD 排序或 Frobenius 失真當作成功 KPI。請以 [正式規格](../PROJECT_SPEC.md) 為準。

## 現況（2026-11-08）

- W0 [#13](https://github.com/Rookie-YCLin/matrix-jpeg-research/pull/13)、W0-D [#14](https://github.com/Rookie-YCLin/matrix-jpeg-research/pull/14)：Q10 原版 12／96、Q20 78／96、Q30 0／96。
- G2 [#17](https://github.com/Rookie-YCLin/matrix-jpeg-research/pull/17)、G3 [#18](https://github.com/Rookie-YCLin/matrix-jpeg-research/pull/18)、G4 [#20](https://github.com/Rookie-YCLin/matrix-jpeg-research/pull/20)、G5 前置 [#21](https://github.com/Rookie-YCLin/matrix-jpeg-research/pull/21) 與嵌入候選 [#22](https://github.com/Rookie-YCLin/matrix-jpeg-research/pull/22) 均已交付未合併的 Draft PR。主條件 Q10 無改善：G3 13／96、G4 17／96、G5 24／96。
- G5 降低排序違反與提高 PNG PSNR，**不是** JPEG BER 改善，也未符合預先設定的品質匹配窗口。G5 改的是**嵌入**，不是只改擷取。
- PR [#19](https://github.com/Rookie-YCLin/matrix-jpeg-research/pull/19) 為未完成正式報告審閱稿；不應把 G5 的數學正確性寫成抗 JPEG 成功。歷史 M0–M4 只作背景資料。

## 下次工作唯一允許的研究前置

先從封存 W0-D 檔案做**唯讀**失效診斷：D0／聚合分數與 K-means；D1／各位元第一、第二奇異值投票率；D2／PNG–JPEG 餘數位移。先用公開 bit API 逐位核對，真實 payload 僅供離線評估，不能引入盲式解碼。診斷結果須區分觀察、假說與因果。**未取得主持人新的實驗授權，不得提交 G6 或新的量化參數搜尋。**

資料與重現方式見 [實驗索引](EXPERIMENT_INDEX.md)。獨立分支、保留 SHA／manifest／CSV／CI，任何合併與刪除研究證據均需研究主持人明確批准。
