# 研究交付章程｜SVD 改良，以 JPEG BER 為目標

**正式目標**：基於 [guofei9987/blind_watermark](https://github.com/guofei9987/blind_watermark) 改良 **SVD 嵌入或擷取方法**，使 JPEG 壓縮後的盲式浮水印 BER 低於原版。詳見 [正式規格](../PROJECT_SPEC.md)。

1. 主要評估 JPEG Q10／4:4:4 的 BER（原版 12／96），Q20、Q30 與無攻擊 PNG 為輔助診斷；PSNR 只作預先設定的影像品質限制。任何正向改善皆須通過同條件配對與獨立驗證，不能只以保序或 PSNR 取代。
2. 固定原版與 G2–G5 的全部正負結果，見 [實驗索引](EXPERIMENT_INDEX.md)、[#20](https://github.com/Rookie-YCLin/matrix-jpeg-research/pull/20)、[#21](https://github.com/Rookie-YCLin/matrix-jpeg-research/pull/21)、[#22](https://github.com/Rookie-YCLin/matrix-jpeg-research/pull/22)。目前尚無主要 Q10 BER 改善。
3. 暫停新的演算法候選，優先用現有證據進行 D0／D1／D2 唯讀失效診斷；需事前核准才可重新啟動候選或改變研究邊界。
4. 正式報告如實呈現原版、干預方法、BER／PSNR 配對數據、限制與負結果。AI 自動審查維持停用。
5. Git 精簡以文件主線、連結與研究決策為優先；歷史碼、CSV、manifest、雜湊、PR、上游授權與 CI 保留，不能為讓結果看似成功而刪除。所有 PR 合併均須研究主持人明確批准。
