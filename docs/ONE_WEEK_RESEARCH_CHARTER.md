# 一週研究章程｜數位浮水印

研究主持人的最新決議見 [Issue #8](https://github.com/Rookie-YCLin/matrix-jpeg-research/issues/8)。研究範圍、公式與比較條件集中在 [PROJECT_SPEC.md](../PROJECT_SPEC.md)。第一個工作包是 [Issue #10](https://github.com/Rookie-YCLin/matrix-jpeg-research/issues/10)。

1. 先凍結上游提交、合法 RGB 影像、payload、密鑰與環境，取得可重現的無攻擊結果。
2. 再完成四種 JPEG 攻擊及原版 BER–PSNR 基準，交付原始數據與測試供審查。基準失敗時保留證據並停在 G1。
3. 基準通過後，在獨立 G2 議題及 PR 比較 d2。報告保留可比品質條件、負結果與失敗案例，主張以配對數據為限。

[PR #7](https://github.com/Rookie-YCLin/matrix-jpeg-research/pull/7) 與 [PR #12](https://github.com/Rookie-YCLin/matrix-jpeg-research/pull/12) 保存歷史成果。先前的 R1 章程與交接仍可在 [Draft PR #9 前版提交](https://github.com/Rookie-YCLin/matrix-jpeg-research/tree/e3e613a50a1ef1eb4efb71938c8193902eb915cf) 追溯。
