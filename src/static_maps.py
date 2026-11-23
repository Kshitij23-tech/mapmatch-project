import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

OUT = Path("results/static_maps"); OUT.mkdir(parents=True, exist_ok=True)
COL = {0: "#e08a00", 1: "#0d8f8f", 2: "#6b7280"}   # main = amber, service = teal, other = grey
NAME = {0: "main", 1: "service", 2: "other"}

pts = pd.read_parquet("data/processed/points.parquet").reset_index(drop=True)
print("points columns:", pts.columns.tolist())
pre = pd.read_parquet("results/real_preds.parquet")

if "idx" not in pts.columns:
    pts["idx"] = pts.groupby("trip").cumcount()

if {"x", "y"}.issubset(pts.columns):
    xc, yc = "x", "y"
elif {"lon", "lat"}.issubset(pts.columns):
    xc, yc = "lon", "lat"
else:
    raise SystemExit("No x/y or lon/lat in points.parquet; send me the 'points columns' line above")

methods = list(pre["method"].unique())
print("methods:", methods)

for trip, d in pts.groupby("trip"):
    d = d.sort_values("idx").reset_index(drop=True)
    panels = [("truth", None)] + [(m, m) for m in methods]
    fig, axs = plt.subplots(1, len(panels), figsize=(5 * len(panels), 6), squeeze=False)
    for ax, (title, m) in zip(axs[0], panels):
        src = pre[(pre["trip"] == trip) & (pre["method"] == (m or methods[0]))]
        col = "true" if m is None else "pred"
        lab = d[["idx", xc, yc]].merge(src[["idx", col]], on="idx", how="inner")
        ax.plot(lab[xc], lab[yc], color="#cccccc", lw=1, zorder=1)
        for k, c in COL.items():
            s = lab[lab[col] == k]
            ax.scatter(s[xc], s[yc], s=8, color=c, label=NAME[k], zorder=2)
        for i in range(0, len(lab), 50):
            ax.annotate(str(lab["idx"][i]), (lab[xc][i], lab[yc][i]), fontsize=7, color="red")
        ax.set_title(f"{trip} - {title}")
        ax.set_aspect("equal")
        ax.legend(loc="best", fontsize=7)
    fig.tight_layout()
    fig.savefig(OUT / f"{trip}.png", dpi=130)
    plt.close(fig)
    print("saved", OUT / f"{trip}.png")