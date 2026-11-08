# DWT–DCT–SVD 盲式浮水印抗 JPEG 研究

研究問題是在相近的含浮水印影像品質下，只調整 SVD 第二奇異值的嵌入步長 d2，能否降低 JPEG 攻擊後的 BER。上游固定為 `guofei9987/blind_watermark` 的 `322c90dc02d45644692095b34d3a6b735b6edbd8`。研究保留原版盲擷取，JPEG 作黑盒攻擊。[上游核心程式](https://github.com/guofei9987/blind_watermark/blob/322c90dc02d45644692095b34d3a6b735b6edbd8/blind_watermark/bwm_core.py) · [研究決策](https://github.com/Rookie-YCLin/matrix-jpeg-research/issues/8)

| 階段 | 進度 |
|---|---|
| W0 | 已交付、待人工驗收。三張圖、固定 payload，無攻擊與各 JPEG Q40/60/80/95 均觀察到 0/96。 [PR #13](https://github.com/Rookie-YCLin/matrix-jpeg-research/pull/13) |
| W0-D | 已交付、待人工驗收。4:4:4 的 Q10、Q20、Q30 分別為 12/96、78/96、0/96。 [PR #14](https://github.com/Rookie-YCLin/matrix-jpeg-research/pull/14) |
| G2 | 待主持人批准，未執行。唯一工作入口為 [Issue #16](https://github.com/Rookie-YCLin/matrix-jpeg-research/issues/16)。 |
| 歷史 | PDF 與 R1 保留，R1 不作浮水印證據。 [PR #7](https://github.com/Rookie-YCLin/matrix-jpeg-research/pull/7) · [PR #12](https://github.com/Rookie-YCLin/matrix-jpeg-research/pull/12) |

[正式規格](PROJECT_SPEC.md) · [實驗索引](docs/EXPERIMENT_INDEX.md) · [三日章程](docs/ONE_WEEK_RESEARCH_CHARTER.md) · [Codex 交接](docs/CODEX_NEXT_SESSION.md)
