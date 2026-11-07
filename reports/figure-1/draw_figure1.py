"""Figure 1 at 156 mm, the text width of the existing A4 report."""
import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
from matplotlib import font_manager, pyplot as plt
from matplotlib.patches import Rectangle
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
DATA = ROOT / "outputs/run-m2"
WIDTH, HEIGHT = 156, 150
QUALITIES = (40, 60, 80, 95)
COLORS = ("#184d80", "#64717c", "#64717c", "#aa4529")
MARKERS = ("o", "s", "^", "D")
INK = "#172737"
ROI = (36, 224, 220, 354)
ZOOM = (62, 267, 164, 299)


def rows(filename):
    with (DATA / filename).open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def source_data():
    metrics = {int(row["quality_factor"]): float(row["psnr_db"])
               for row in rows("jpeg_metrics.csv")}
    rank = {row["image"]: 100 * float(row["relative_squared"])
            for row in rows("rank_errors.csv") if row["k"] == "100"}
    return [metrics[q] for q in QUALITIES], [rank[f"jpeg_q{q}"] for q in QUALITIES], rank["original"]


def main():
    fonts = Path("C:/Windows/Fonts")
    for filename in ("times.ttf", "timesbd.ttf", "kaiu.ttf"):
        font_manager.fontManager.addfont(fonts / filename)
    chinese = font_manager.FontProperties(fname=fonts / "kaiu.ttf")
    plt.rcParams.update({
        "font.family": "Times New Roman",
        "font.size": 9,
        "pdf.fonttype": 42,
        "mathtext.fontset": "stix",
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.edgecolor": "#5b6570",
        "axes.linewidth": .6,
        "xtick.major.size": 3,
        "ytick.major.size": 3,
        "text.color": INK,
    })
    figure = plt.figure(figsize=(WIDTH / 25.4, HEIGHT / 25.4), facecolor="white")

    def axes(x, y, width, height):
        return figure.add_axes([x / WIDTH, y / HEIGHT, width / WIDTH, height / HEIGHT])

    def text(x, y, label, *, size=10, kai=True, **kwargs):
        figure.text(x / WIDTH, y / HEIGHT, label, fontsize=size,
                    fontproperties=chinese if kai else None, va="center", **kwargs)

    def heading(x, y, tag, title):
        text(x, y, tag, size=11, kai=False, fontweight="bold")
        text(x + 8, y, title, size=11)

    heading(2, 146, "(a)", "同一區域，三種像素結果")
    sources = (
        ("原圖", ROOT / "data/ascent.png", INK),
        ("Q=40 解碼", DATA / "jpeg_q40_decoded.png", COLORS[0]),
        ("Q=95 解碼", DATA / "jpeg_q95_decoded.png", COLORS[3]),
    )
    zoom_pixels = []
    for _, path, _ in sources:
        with Image.open(path) as image:
            zoom_pixels.append(np.array(image.crop(ZOOM), dtype=np.int16))
    differences = [np.abs(pixels - zoom_pixels[0]) for pixels in zoom_pixels[1:]]
    ceiling = max(1, *(int(diff.max()) for diff in differences))
    for i, (x, (label, path, color)) in enumerate(zip((3, 55, 107), sources, strict=True)):
        text(x + 23, 138.5, label, ha="center", color=color)
        overview = axes(x, 103, 46, 32.5)
        detail = axes(x, 85, 46, 14.45)
        with Image.open(path) as image:
            overview.imshow(image.crop(ROI), cmap="gray", vmin=0, vmax=255, interpolation="nearest")
        if i:
            detail.imshow(differences[i - 1], cmap="gray", vmin=0, vmax=ceiling,
                          interpolation="nearest")
        else:
            detail.text(.5, .64, "黃框內的絕對像素差", ha="center", va="center",
                        fontproperties=chinese, fontsize=10)
            detail.text(.5, .31, f"黑 = 0，白 = {ceiling}", ha="center", va="center",
                        fontproperties=chinese, fontsize=9)
        overview.add_patch(Rectangle(
            (ZOOM[0] - ROI[0] - .5, ZOOM[1] - ROI[1] - .5),
            ZOOM[2] - ZOOM[0], ZOOM[3] - ZOOM[1],
            edgecolor="#ffe681", linewidth=1, facecolor="none",
        ))
        for axis in (overview, detail):
            axis.set_axis_off()
    text(78, 81, "上排共用原始灰階。下排差值另用共同灰階映射。", size=9, ha="center")

    psnr, rank, original = source_data()
    heading(2, 74, "(b)", "與原圖比較")
    heading(81, 74, "(c)", "各圖與自身 Rank-100 比較")
    for x, values, digits, lim, ticks, unit in (
        (12, psnr, 2, (29, 51), [30, 35, 40, 45, 50], "PSNR (dB)"),
        (95, rank, 5, (.442, .560), [.45, .48, .51, .54], "相對平方誤差 (%)"),
    ):
        axis = axes(x, 34, 56, 32)
        axis.set(xlim=(32, 104), ylim=lim, xticks=QUALITIES, yticks=ticks)
        axis.set_title(unit, loc="left", fontproperties=chinese, fontsize=9, pad=4)
        axis.set_xlabel("JPEG 品質因子 Q", fontproperties=chinese, fontsize=9, labelpad=3)
        axis.tick_params(labelsize=8.5)
        axis.set_axisbelow(True)
        axis.grid(axis="y", linewidth=.55, color="#dce2e7")
        if digits == 5:
            axis.axhline(original, linestyle=(0, (4, 2)), linewidth=.8, color="#46525d")
            axis.text(102, original - .0055, f"原圖 {original:.5f}%",
                      ha="right", va="top", fontproperties=chinese, fontsize=8.5,
                      bbox={"facecolor": "white", "edgecolor": "none", "pad": .8})
        axis.plot(QUALITIES, values, color="#8a969e", linewidth=.85, linestyle=(0, (3, 2)))
        for q, value, color, marker in zip(QUALITIES, values, COLORS, MARKERS, strict=True):
            axis.scatter(q, value, c=color, marker=marker, s=31, zorder=3)
            if q in (40, 95):
                axis.annotate(f"{value:.{digits}f}", (q, value), xytext=(0, 5),
                              textcoords="offset points", ha="center", va="bottom", fontsize=9)

    heading(2, 18, "(d)", "兩種比較各自減去什麼？")
    for x, pair, detail in (
        (2, r"$A-B_Q$", "原圖減去 JPEG 解碼圖"),
        (81, r"$B_Q-(B_Q)_{100}$", "解碼圖減去自身截斷重建"),
    ):
        box = axes(x, 2.5, 73, 11)
        box.set_axis_off()
        box.add_patch(Rectangle((0, 0), 1, 1, transform=box.transAxes,
                                facecolor="#eef3f6", edgecolor="none"))
        box.text(.5, .68, pair, ha="center", va="center", fontsize=11, color=INK)
        box.text(.5, .24, detail, ha="center", va="center", fontsize=9, fontproperties=chinese)
    figure.savefig(HERE / "FIGURE_1.pdf", dpi=300,
                   metadata={"Title": "Figure 1 | JPEG fidelity and self rank-100 error"})
    plt.close(figure)


if __name__ == "__main__":
    main()
