# 專題執行章程｜原版基準 → SVD 改良 → 正向結果

以 [guofei9987/blind_watermark](https://github.com/guofei9987/blind_watermark) 固定版為 Source Code，目標是**改善低 JPEG Quality Factor 下的浮水印 BER**。正式評估指標只有不同 QF 的 BER；不要求 PSNR。

1. **先測原版**：以上游 [bwm_core.py](https://github.com/guofei9987/blind_watermark/blob/master/blind_watermark/bwm_core.py) 為基準；自行補上 [att.py](https://github.com/guofei9987/blind_watermark/blob/master/blind_watermark/att.py) 所缺少的 JPEG 壓縮攻擊測試。固定圖片、bit、密鑰、編碼器及 QF，逐圖比較 BER。
2. **只改 SVD**：獨立設計並測試嵌入及／或擷取方法；把矩陣理論用來解釋方法，不能以理論證明替代壓縮後的 BER 實測。
3. **迭代至可重現的 BER 改善**：未改善就記錄並設計下個候選；取得事前界定低 QF 的可重現正向結果即可停止。新正式測試與重要選擇須向主持人說明、取得同意。
4. **報告精簡**：正式報告主要呈現成功方法與 BER–QF 結果，不必列舉失敗候選；所有內部實驗仍保留，以確保真實、可追溯。
5. **GitHub 管理與回報**：每輪使用本倉庫獨立分支／Draft PR；新增、修改、刪除皆需說明依賴與影響，不能擅自刪除證據或合併 main。主動提供階段、成果、各 QF BER、風險、下一步及待決事項。

詳見 [正式規格](../PROJECT_SPEC.md)、[實驗索引](EXPERIMENT_INDEX.md)。
