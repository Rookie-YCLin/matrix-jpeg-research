"""Render publication figures from the archived M2 CSVs and image panels."""
import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
from matplotlib import font_manager, pyplot as plt
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "outputs/run-m2"
DEST = ROOT / "reports/figures"
QUALITIES = (40, 60, 80, 95)
STYLES = {
    40: ("#143b68", "-", "o"),
    60: ("#a94716", "--", "s"),
    80: ("#117364", "-.", "^"),
    95: ("#744c8b", ":", "D"),
}
BASELINE = "#30343b"


def rows(name):
    with (DATA / f"{name}.csv").open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def setup():
    for name in ("times.ttf", "timesbd.ttf", "timesi.ttf"):
        path = Path("C:/Windows/Fonts") / name
        font_manager.fontManager.addfont(path)
    plt.rcParams.update({
        "font.family": "Times New Roman",
        "font.size": 12,
        "axes.labelsize": 12,
        "xtick.labelsize": 11,
        "ytick.labelsize": 11,
        "legend.fontsize": 10.5,
        "mathtext.fontset": "stix",
        "pdf.fonttype": 42,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.axisbelow": True,
        "axes.grid": True,
        "grid.color": "#e1e4e8",
        "grid.linewidth": 0.55,
        "lines.linewidth": 1.6,
        "savefig.facecolor": "white",
    })
    DEST.mkdir(exist_ok=True)


def save(figure, name):
    figure.savefig(DEST / f"{name}.pdf", dpi=300)
    plt.close(figure)


def series(axis, x, y, q, *, every=None):
    color, dash, marker = STYLES[q]
    axis.plot(x, y, label=f"Q = {q}", color=color, linestyle=dash,
              marker=marker if every else None, markevery=every, markersize=5,
              markerfacecolor="white")


def legend(axis, **kwargs):
    axis.legend(frameon=False, ncols=2, **kwargs)


def workflow():
    figure, axis = plt.subplots(figsize=(6.05, 3.65))
    kai = font_manager.FontProperties(fname="C:/Windows/Fonts/kaiu.ttf")
    axis.set(xlim=(0, 1), ylim=(0, 1))
    axis.set_axis_off()

    def box(x, y, label, *, highlight=False):
        axis.text(x, y, label, ha="center", va="center", linespacing=1.35, fontproperties=kai,
                  bbox={"boxstyle": "round,pad=0.48", "edgecolor": "#354764",
                        "facecolor": "#edf3fa" if highlight else "white"})

    def arrow(start, end):
        axis.annotate("", xy=end, xytext=start,
                      arrowprops={"arrowstyle": "->", "color": "#354764", "lw": 1.25})

    box(.5, .9, "灰階原圖 A\n512 × 512", highlight=True)
    box(.25, .64, "全圖 SVD\n固定原圖秩一方向")
    box(.75, .64, "JPEG 編碼再解碼\nQ = 40, 60, 80, 95")
    box(.75, .40, r"解碼矩陣 $B_Q$", highlight=True)
    arrow((.44, .81), (.29, .72))
    arrow((.56, .81), (.71, .72))
    arrow((.75, .56), (.75, .46))
    for x, label in [
        (.18, "沿原圖方向\n有號投影"),
        (.50, "相對原圖\nMSE 與 PSNR"),
        (.85, "解碼圖 SVD\n頻譜與自身誤差"),
    ]:
        box(x, .10, label)
        arrow((.75, .34), (x, .19))
    arrow((.22, .55), (.18, .19))
    save(figure, "workflow")


def quality_figures(metrics, errors):
    figure, axes = plt.subplots(2, 1, figsize=(6.05, 4.35), sharex=True, layout="constrained")
    psnr = [float(r["psnr_db"]) for r in metrics]
    rank100 = {r["image"]: 100 * float(r["relative_squared"])
               for r in errors if r["k"] == "100"}
    own = [rank100[f"jpeg_q{q}"] for q in QUALITIES]
    for axis, values in zip(axes, (psnr, own), strict=True):
        axis.plot(QUALITIES, values, color="#616a78", linewidth=1.2)
        for q, value in zip(QUALITIES, values, strict=True):
            color, _, marker = STYLES[q]
            axis.scatter(q, value, c=color, marker=marker, s=35, zorder=4)
    axes[0].set(ylabel="PSNR to original (dB)", ylim=(29, 50))
    axes[1].set(ylabel="Self rank-100 error (%)", xlabel="JPEG quality factor Q",
                ylim=(.44, .56), xticks=QUALITIES)
    axes[1].axhline(rank100["original"], color=BASELINE, linestyle="--", linewidth=1)
    axes[1].text(42, .518, "Original", fontsize=10, va="bottom")
    for axis, values, digits in ((axes[0], psnr, 2), (axes[1], own, 3)):
        for i in (0, 3):
            axis.annotate(f"{values[i]:.{digits}f}", (QUALITIES[i], values[i]),
                          xytext=(0, 8), textcoords="offset points", ha="center", fontsize=10)
    save(figure, "quality")

    figure, axis = plt.subplots(figsize=(6.05, 2.75), layout="constrained")
    for q, row in zip(QUALITIES, metrics, strict=True):
        size = int(row["jpeg_bytes"]) / 1000
        value = float(row["psnr_db"])
        color, _, marker = STYLES[q]
        axis.scatter(size, value, c=color, marker=marker, s=44)
        axis.annotate(f"Q = {q}", (size, value), xytext=((-8 if q == 95 else 8), -1),
                      textcoords="offset points", ha="right" if q == 95 else "left")
    axis.set(xlabel="JPEG file size (kB; 1 kB = 1000 bytes)", ylabel="PSNR (dB)",
             xlim=(18, 98), ylim=(30, 48))
    save(figure, "size_fidelity")


def low_rank_figures(errors, spectrum):
    figure, (axis, inset) = plt.subplots(2, 1, figsize=(6.05, 4.45), layout="constrained",
                                         height_ratios=(2.0, 1.0))
    sample_ranks = {1, 5, 10, 20, 50, 100}
    baseline = {int(r["k"]): 100 * float(r["relative_squared"])
                for r in errors if r["image"] == "original"}
    for q in (None, *QUALITIES):
        name = "original" if q is None else f"jpeg_q{q}"
        group = [r for r in errors if r["image"] == name and int(r["k"]) in sample_ranks]
        ranks = [int(r["k"]) for r in group]
        values = [100 * float(r["relative_squared"]) for r in group]
        if q is None:
            axis.plot(ranks, values, "k-", alpha=.75, label="Original", marker="x")
        else:
            series(axis, ranks, values, q, every=1)
        if q is not None:
            late = [(k, value - baseline[k]) for k, value in zip(ranks, values) if k >= 50]
            x, y = zip(*late)
            series(inset, x, y, q, every=1)
    axis.set(xscale="log", yscale="log", ylabel="Self error (%)", xticks=sorted(sample_ranks),
             xlabel="Retained rank k")
    axis.set_xticks(sorted(sample_ranks), labels=sorted(sample_ranks))
    legend(axis, loc="upper right")
    inset.axhline(0, color=BASELINE, linewidth=.85)
    inset.set(xlabel="Retained rank k", ylabel="vs. original (pp)", xticks=[50, 100])
    save(figure, "rank_error")

    figure, axis = plt.subplots(figsize=(6.05, 3.12), layout="constrained")
    for q in (None, *QUALITIES):
        group = [r for r in spectrum if r["image"] == ("original" if q is None else f"jpeg_q{q}")]
        x = [int(r["i"]) for r in group]
        y = [float(r["sigma"]) for r in group]
        if q is None:
            axis.plot(x, y, color=BASELINE, label="Original", linewidth=2)
        else:
            series(axis, x, y, q, every=(32 + QUALITIES.index(q)*9, 81))
    axis.axvline(400, color="#8c949d", linewidth=.8, linestyle="--")
    axis.annotate("i = 400", (400, 70), xytext=(8, 8), textcoords="offset points")
    axis.set(xlabel="Singular-value index i", ylabel="Singular value", yscale="symlog",
             xlim=(1, 512), ylim=(0, 65000))
    legend(axis, loc="upper right")
    save(figure, "spectrum")


def images():
    originals = [("Original", ROOT / "data/ascent.png")]
    panels = originals + [(f"Rank {k}", DATA / f"rank_{k:03}.png") for k in (1, 5, 10, 20, 50, 100)]
    panels += [("JPEG Q = 80", DATA / "jpeg_q80_decoded.png")]
    figure, axes = plt.subplots(2, 4, figsize=(6.05, 3.4), layout="constrained")
    for axis, (name, path) in zip(axes.flat, panels, strict=True):
        with Image.open(path) as image:
            axis.imshow(image.copy(), cmap="gray", vmin=0, vmax=255, interpolation="nearest")
        axis.set_title(name, fontsize=11)
        axis.set_axis_off()
    save(figure, "reconstruction")

    crop = (34, 223, 218, 407)
    figure, axes = plt.subplots(2, 3, figsize=(6.05, 4.35), layout="constrained")
    for axis, (name, path) in zip(axes.flat, [panels[i] for i in (0, 3, 5, 6, 7)]):
        with Image.open(path) as image:
            axis.imshow(image.crop(crop), cmap="gray", vmin=0, vmax=255, interpolation="nearest")
        axis.set_title(name)
        axis.set_axis_off()
    axes.flat[-1].set_axis_off()
    axes.flat[-1].text(.05, .60, "Shared crop\nx: [34, 218)\ny: [223, 407)\n\nShared gray scale\n0 to 255",
                       transform=axes.flat[-1].transAxes, va="center", fontsize=11)
    save(figure, "detail")


def projections(data):
    figure, (axis, detail) = plt.subplots(2, 1, figsize=(6.05, 4.65), layout="constrained",
                                          height_ratios=(2.2, 1.1))
    for q in QUALITIES:
        group = [r for r in data if int(r["quality_factor"]) == q]
        i = [int(r["i"]) for r in group]
        delta = [float(r["delta"]) for r in group]
        series(axis, i, delta, q, every=(12+QUALITIES.index(q)*8, 94))
        selected = next(float(r["coefficient"]) for r in group if r["i"] == "512")
        color, _, marker = STYLES[q]
        detail.scatter(q, selected, c=color, marker=marker, s=42)
        detail.annotate(f"{selected:+.2f}", (q, selected), xytext=(0, 7),
                        textcoords="offset points", ha="center", fontsize=10)
    axis.axhline(0, color=BASELINE, linewidth=.8)
    axis.axvline(200, color="#858e9a", linestyle="--", linewidth=.85)
    axis.set(xlabel="Original direction index i", ylabel="Signed change",
             xlim=(1, 512), ylim=(-113, 78))
    legend(axis, loc="lower right")
    detail.axhline(0, color=BASELINE, linewidth=.85)
    detail.set(xlabel="JPEG quality factor Q", ylabel="Coefficient at i = 512",
               xticks=QUALITIES, ylim=(-2.3, 5.6), xlim=(35, 100))
    save(figure, "projection")


def main():
    setup()
    workflow()
    errors = rows("rank_errors")
    quality_figures(rows("jpeg_metrics"), errors)
    low_rank_figures(errors, rows("spectrum"))
    images()
    projections(rows("projections"))


if __name__ == "__main__":
    main()
