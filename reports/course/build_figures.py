"""Build report figures from fixed CSVs and reproduced paired PSNR artifacts."""
import argparse
import csv
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
BER = ROOT / "outputs/svd-qim-qf15-selected"
PSNR = ROOT / "outputs/svd-qim-psnr-qf15"
COLORS = ("#254f73", "#ad4f24")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rows(path):
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def save(fig, out, name):
    fig.savefig(out / f"{name}.png", dpi=220, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def image_panel(paths, titles, out, name, crop=None):
    fig, axes = plt.subplots(1, len(paths), figsize=(7.4, 3.45))
    for ax, path, title in zip(axes, paths, titles):
        with Image.open(path) as img:
            ax.imshow(img.crop(crop) if crop else img)
        ax.set_title(title, fontsize=10)
        ax.axis("off")
    save(fig, out, name)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--paired", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    out, paired = args.output, args.paired
    archive = json.loads((PSNR / "manifest.json").read_text(encoding="utf-8"))
    for name, digest in archive["files_sha256"].items():
        if sha(paired / name) != digest:
            raise ValueError(f"Reproduced artifact differs: {name}")
    out.mkdir(parents=True, exist_ok=False)
    names = ("ori_img.jpeg", "upstream_qf15.jpg", "svd_step_90_qf15.jpg")
    image_panel([paired / n for n in names], ["Reference RGB", "Original QF15", "G6 QF15"], out, "paired")
    crop = (160, 360, 480, 680)
    image_panel([paired / n for n in names], ["Reference RGB", "Original QF15", "G6 QF15"], out, "paired_crop", crop)
    sealed = json.loads((BER / "manifest.json").read_text(encoding="utf-8"))["files_sha256"]
    paths = []
    replay_matches = {}
    with Image.open(paired / "upstream_marked.png") as img:
        for quality in (5, 15, 50, 95):
            path = out / f"original-qf{quality:02}.jpg"
            img.save(path, "JPEG", quality=quality, subsampling=0, optimize=False, progressive=False)
            replay_matches[str(quality)] = sha(path) == sealed[f"primary_upstream_qf{quality:02}.jpg"]
            paths.append(path)
    image_panel(paths, ["QF5", "QF15", "QF50", "QF95"], out, "quality", crop)

    fig, ax = plt.subplots(figsize=(7.1, 3.35))
    for variant, label, color, marker in zip(("upstream", "svd_step_90"), ("Original (36,20)", "G6 (90,20)"), COLORS, ("o", "x")):
        points = sorted((int(r["qf"]), 100 * float(r["ber"])) for r in rows(BER / "results.csv")
                        if r["payload"] == "primary" and r["variant"] == variant)
        ax.plot(*zip(*points), color=color, marker=marker, label=label)
    ax.set(xlabel="JPEG quality factor", ylabel="BER (%)", xticks=range(5, 100, 10), ylim=(-5, 108))
    ax.axvline(15, color="#666666", linestyle=":", linewidth=1)
    ax.grid(alpha=.22)
    ax.legend()
    save(fig, out, "ber",)

    fig, ax = plt.subplots(figsize=(7, 3.1))
    vals = {(r["variant"], r["stage"]): float(r["psnr_db"]) for r in rows(PSNR / "results.csv")}
    for j, (variant, label) in enumerate((("upstream", "Original"), ("svd_step_90", "G6"))):
        bars = ax.bar([j*.32, 1+j*.32], [vals[variant,s] for s in ("uncompressed_embedded","qf15_attacked")], .29, color=COLORS[j],label=label)
        ax.bar_label(bars, fmt="%.3f", padding=2)
    ax.set(xticks=(.16,1.16), xticklabels=("Marked PNG","JPEG QF15"), ylabel="PSNR (dB)", ylim=(0,47))
    ax.legend()
    save(fig, out, "psnr")

    fig, axes = plt.subplots(2, 1, figsize=(7.1, 2.7), sharex=True)
    for ax, d in zip(axes,(36,90)):
        ax.axvspan(0,d/2,color=COLORS[0],alpha=.12)
        ax.axvspan(d/2,d,color=COLORS[1],alpha=.12)
        ax.hlines(0,0,d,color="#333333")
        for b,x in enumerate((d/4,3*d/4)):
            ax.scatter(x,0,c=COLORS[b],zorder=3)
            ax.text(x,.13,f"bit {b}: {x:g}",ha="center")
        ax.text(d/2,-.21,f"boundary {d/2:g}",ha="center")
        ax.set(ylim=(-.36,.35),yticks=[],ylabel=f"d={d}")
        ax.spines[["top","left","right"]].set_visible(False)
    axes[-1].set_xlabel("Remainder (singular-value units) · schematic")
    save(fig,out,"qim")
    fig, ax = plt.subplots(figsize=(7.2, 2.5))
    ax.set_axis_off()
    for y, labels in (
        (.74, ["RGB input", "Haar DWT\nlow band", "4×4 DCT\npermute", "SVD → QIM", "Inverse path\nmarked PNG"]),
        (.25, ["JPEG decode", "Same block\ntransform", "Sorted SVD", "Modulo votes\n3:1 fusion", "Average → K-means\nrestore bit order"]),
    ):
        for i, label in enumerate(labels):
            x = .10 + .20*i
            ax.text(x, y, label, ha="center", va="center", transform=ax.transAxes,
                    fontsize=9, bbox={"facecolor":"#edf3f8","edgecolor":"#667f91","pad":4})
            if i:
                ax.annotate("", xy=(x-.087,y), xytext=(x-.12,y), xycoords="axes fraction",
                            arrowprops={"arrowstyle":"->","color":"#4d5b66"})
    save(fig, out, "flow")
    (out / "provenance.json").write_text(json.dumps({
        "source_sha256":archive["source_sha256"], "upstream":archive["upstream"],
        "jpeg":archive["jpeg"], "crop_xyxy":crop, "illustrative_qf_matches_sealed_bytes":replay_matches,
        "figure_sha256":{p.name:sha(p) for p in sorted(out.iterdir()) if p.is_file()},
    }, indent=2),encoding="utf-8")


if __name__ == "__main__":
    main()
