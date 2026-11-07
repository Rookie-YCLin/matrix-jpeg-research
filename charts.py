"""Render figures from the CSV and PNG artifacts of a single run."""
import csv
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
from matplotlib import pyplot as plt
from PIL import Image


def read_rows(path):
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def render(output, input_pixels, ranks, labels, preview_quality, preview_name):
    figure, axes = plt.subplots(2, 4, figsize=(12, 6), layout="constrained")
    images = [("Original", input_pixels)]
    images += [(f"Rank {k}", output / f"rank_{k:03}.png") for k in ranks]
    images += [(f"JPEG Q={preview_quality} decoded", output / preview_name)]
    for axis, (title, image) in zip(axes.flat, images, strict=True):
        if isinstance(image, Path):
            with Image.open(image) as png:
                axis.imshow(png, cmap="gray", vmin=0, vmax=255)
        else:
            axis.imshow(image, cmap="gray", vmin=0, vmax=255)
        axis.set_title(title)
        axis.set_axis_off()
    figure.savefig(output / "reconstructions.png", dpi=150)
    plt.close(figure)

    rows = read_rows(output / "rank_errors.csv")
    figure, axis = plt.subplots(figsize=(8, 4), layout="constrained")
    for name, label in labels.items():
        group = [row for row in rows if row["image"] == name and int(row["k"]) in ranks]
        axis.plot([int(row["k"]) for row in group],
                  [float(row["relative_squared"]) for row in group], "o-", label=label)
    axis.set(xlabel="Rank k", ylabel="Relative squared Frobenius error")
    axis.set_xscale("log")
    axis.set_xticks(ranks, labels=ranks)
    axis.legend()
    figure.savefig(output / "rank_errors.png", dpi=150)
    plt.close(figure)

    rows = read_rows(output / "spectrum.csv")
    figure, (spectrum, energy) = plt.subplots(1, 2, figsize=(11, 4), layout="constrained")
    for name, label in labels.items():
        group = [row for row in rows if row["image"] == name]
        indices = [int(row["i"]) for row in group]
        spectrum.plot(indices, [float(row["sigma"]) for row in group], label=label)
        energy.plot(indices, [float(row["cumulative_energy"]) for row in group], label=label)
    spectrum.set(xlabel="Singular value index", ylabel="Singular value")
    spectrum.set_yscale("symlog", linthresh=1)
    energy.set(xlabel="Number of components", ylabel="Cumulative squared energy fraction")
    energy.set_xscale("log")
    for axis in (spectrum, energy):
        axis.legend()
    figure.savefig(output / "spectra.png", dpi=150)
    plt.close(figure)


def projection_figure(rows):
    figure, (coefficients, delta) = plt.subplots(2, 1, figsize=(10, 7), layout="constrained")
    qualities = list(dict.fromkeys(row["quality_factor"] for row in rows))
    baseline = [row for row in rows if row["quality_factor"] == qualities[0]]
    coefficients.plot([int(row["i"]) for row in baseline],
                      [float(row["original_sigma"]) for row in baseline],
                      label="Original singular values", color="black", linestyle="--")
    for quality in qualities:
        group = [row for row in rows if row["quality_factor"] == quality]
        indices = [int(row["i"]) for row in group]
        coefficients.plot(indices, [float(row["coefficient"]) for row in group], label=f"Q={quality}")
        delta.plot(indices, [float(row["delta"]) for row in group], label=f"Q={quality}")
    coefficients.set(ylabel="Signed projection coefficient", xlabel="Original direction index")
    coefficients.set_yscale("symlog", linthresh=1)
    delta.set(ylabel="Coefficient minus original singular value", xlabel="Original direction index")
    for axis in (coefficients, delta):
        axis.legend()
    return figure


def quality_figure(rows):
    figure, axis = plt.subplots(figsize=(7, 4), layout="constrained")
    for row in rows:
        size = int(row["jpeg_bytes"])
        psnr = float(row["psnr_db"])
        if psnr == float("inf"):
            axis.text(0.02, 0.98, "Infinite PSNR values are listed in the CSV",
                      transform=axis.transAxes, va="top")
            continue
        axis.plot(size, psnr, "o")
        axis.annotate(f'Q={row["quality_factor"]}', (size, psnr),
                      xytext=(5, 4), textcoords="offset points")
    axis.set(xlabel="Actual JPEG file size (bytes)", ylabel="PSNR (dB)")
    return figure


def render_comparison(output):
    for filename, build in (("projections", projection_figure), ("jpeg_metrics", quality_figure)):
        figure = build(read_rows(output / f"{filename}.csv"))
        figure.savefig(output / f"{filename}.png", dpi=150)
        plt.close(figure)
