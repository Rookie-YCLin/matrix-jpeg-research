# 三日研究交付章程

研究問題與上游公式見 [PROJECT_SPEC.md](../PROJECT_SPEC.md)。[實驗索引](EXPERIMENT_INDEX.md) 保存已完成的基準及驗收證據。[Issue #16](https://github.com/Rookie-YCLin/matrix-jpeg-research/issues/16) 是唯一 G2 工作入口，三日安排以研究主持人批准基準與 G2 設計為前提。

1. 第一天完成管理整合及基準人工審查，凍結攻擊條件與相近 PSNR 門檻，重現 d2=20 對照。
2. 第二天完成單因子配對實驗、重跑和回歸測試。只保留交件所需 CSV、manifest、圖表資料及證據。
3. 第三天完成書面報告。交代上游公式、配對設計、BER–PSNR 結果、失敗案例與樣本限制。一張由 CSV 生成的圖或表即可支撐主要比較。若驗收未完成，照實交代已驗證的 W0/W0-D 與缺口。

AI 自動審查暫不啟用，人工驗收與 Research CI 即為本輪交付流程。
