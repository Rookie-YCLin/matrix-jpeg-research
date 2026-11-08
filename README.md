# 盲式浮水印的 JPEG 抗壓縮與 SVD 區塊演算法

以 `guofei9987/blind_watermark` 固定提交 `322c90dc02d45644692095b34d3a6b735b6edbd8` 為基礎。在相同含水印影像與 JPEG 黑盒攻擊下，只修改 SVD 區塊的擷取判決，檢驗是否能降低逐位 BER。保留原版嵌入及其餘擷取流程。[上游核心程式](https://github.com/guofei9987/blind_watermark/blob/322c90dc02d45644692095b34d3a6b735b6edbd8/blind_watermark/bwm_core.py) · [研究決策](https://github.com/Rookie-YCLin/matrix-jpeg-research/issues/8)

| 階段 | 交付與定位 |
|---|---|
| W0 | 原版基準已交付，待人工驗收。 [PR #13](https://github.com/Rookie-YCLin/matrix-jpeg-research/pull/13) |
| W0-D | JPEG 壓力與判決分數診斷已交付，待人工驗收。 [PR #14](https://github.com/Rookie-YCLin/matrix-jpeg-research/pull/14) |
| G2 | d2 單因子探索已交付，待人工驗收。主要 Q10 未觀察到相近品質下的 BER 改善。 [PR #17](https://github.com/Rookie-YCLin/matrix-jpeg-research/pull/17) |
| G3 | 正式演算法階段。區塊軟判決的實測已交付，待人工驗收。主要 Q10 由 12/96 變為 13/96，未達改善目標。 [PR #18](https://github.com/Rookie-YCLin/matrix-jpeg-research/pull/18) |

[正式規格](PROJECT_SPEC.md) · [實驗索引](docs/EXPERIMENT_INDEX.md) · [研究章程](docs/ONE_WEEK_RESEARCH_CHARTER.md) · [Codex 交接](docs/CODEX_NEXT_SESSION.md)
