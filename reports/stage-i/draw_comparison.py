"""Render the stage-I comparison from the archived M2 results."""
import csv
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from PIL import Image
from matplotlib.font_manager import FontProperties
from draw_final_figures import DATA, ROOT, STYLES, plt, setup

HERE = Path(__file__).resolve().parent
KAI = FontProperties(fname="C:/Windows/Fonts/kaiu.ttf")


def strip(name, panels):
    figure, axes = plt.subplots(1, len(panels), figsize=(6.05, 1.55),
                                layout="constrained")
    for axis, (label, path) in zip(axes, panels, strict=True):
        with Image.open(path) as image:
            axis.imshow(image.crop((34, 223, 218, 407)), cmap="gray", vmin=0, vmax=255)
        axis.set_title(label, fontproperties=KAI, fontsize=12, pad=4)
        axis.set_axis_off()
    figure.savefig(HERE / f"{name}.png", dpi=240)
    plt.close(figure)


def read(name):
    with (DATA / name).open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def main():
    setup()
    q = list(STYLES)
    psnr = {int(r["quality_factor"]): float(r["psnr_db"]) for r in read("jpeg_metrics.csv")}
    rank = {r["image"]: 100 * float(r["relative_squared"])
            for r in read("rank_errors.csv") if int(r["k"]) == 100}
    original = ROOT / "data/ascent.png"
    strip("jpeg-crops", [("原圖", original), ("Q=40 解碼", DATA / "jpeg_q40_decoded.png"),
                        ("Q=95 解碼", DATA / "jpeg_q95_decoded.png")])
    strip("rank-crops", [("原圖", original), *[(f"保留 {k} 項", DATA / f"rank_{k:03}.png")
                                               for k in (1, 10, 50, 100)]])
    figure, axes = plt.subplots(2, 1, figsize=(6.05, 3.0), sharex=True, layout="constrained")
    for axis, values, label, digits in (
        (axes[0], [psnr[k] for k in q], "與原圖比較｜PSNR (dB)", 2),
        (axes[1], [rank[f"jpeg_q{k}"] for k in q], "各圖與自身 Rank-100 比較｜相對平方誤差 (%)", 5),
    ):
        axis.plot(q, values, color="#6a7480", linewidth=1.2)
        for quality, value in zip(q, values, strict=True):
            color, _, marker = STYLES[quality]
            axis.scatter(quality, value, color=color, marker=marker, s=48, zorder=4)
            axis.annotate(f"{value:.{digits}f}", (quality, value),
                          xytext=(0, 6),
                          textcoords="offset points", ha="center", fontsize=10.5)
        axis.set_title(label, fontproperties=KAI, fontsize=12, loc="left")
        axis.tick_params(axis="y", labelsize=10)
        axis.grid(axis="x", visible=False)
    axes[0].set(ylim=(29, 51), yticks=[30, 35, 40, 45, 50])
    axes[1].axhline(rank["original"], color="#495057", linestyle="--", linewidth=1)
    axes[1].text(99, rank["original"] - .006, "原圖自身 0.51677%",
                 fontproperties=KAI, fontsize=10, va="top", ha="right")
    axes[1].set(ylim=(.445, .559), yticks=[.45, .48, .51, .54],
                xlim=(34, 101), xticks=q)
    axes[1].set_xlabel("JPEG 品質因子 Q", fontproperties=KAI, fontsize=12)
    figure.savefig(Path(__file__).with_name("COMPARISON.pdf"))
    plt.close(figure)


if __name__ == "__main__":
    main()
