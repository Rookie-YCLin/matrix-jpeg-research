"""Render the stage-I comparison from the archived M2 results."""
import csv
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from draw_final_figures import DATA, STYLES, plt, setup


def read(name):
    with (DATA / name).open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def main():
    setup()
    q = list(STYLES)
    psnr = {int(r["quality_factor"]): float(r["psnr_db"]) for r in read("jpeg_metrics.csv")}
    rank = {r["image"]: 100 * float(r["relative_squared"])
            for r in read("rank_errors.csv") if int(r["k"]) == 100}
    figure, axes = plt.subplots(2, 1, figsize=(6.05, 4.0), sharex=True, layout="constrained")
    for axis, values, label, digits in (
        (axes[0], [psnr[k] for k in q], "PSNR to original (dB)", 2),
        (axes[1], [rank[f"jpeg_q{k}"] for k in q], "Self rank-100 error (%)", 5),
    ):
        axis.plot(q, values, color="#6a7480", linewidth=1.2)
        for i, (quality, value) in enumerate(zip(q, values, strict=True)):
            color, _, marker = STYLES[quality]
            axis.scatter(quality, value, color=color, marker=marker, s=48, zorder=4)
            axis.annotate(f"{value:.{digits}f}", (quality, value),
                          xytext=(0, 9 if i != 1 or digits == 2 else -17),
                          textcoords="offset points", ha="center", fontsize=10.5)
        axis.set_ylabel(label)
        axis.grid(axis="x", visible=False)
    axes[0].set(ylim=(29, 51), yticks=[30, 35, 40, 45, 50])
    axes[1].axhline(rank["original"], color="#495057", linestyle="--", linewidth=1)
    axes[1].text(99, rank["original"] - .003, "Original-image baseline",
                 fontsize=10, va="top", ha="right")
    axes[1].set(ylim=(.445, .559), yticks=[.45, .48, .51, .54],
                xlim=(34, 101), xticks=q, xlabel="JPEG quality factor Q")
    figure.savefig(Path(__file__).with_name("COMPARISON.pdf"))
    plt.close(figure)


if __name__ == "__main__":
    main()
