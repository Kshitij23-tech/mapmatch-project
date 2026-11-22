"""Helpers for writing data/labels.csv: a numbered map and a speed/height plot for each dataset."""
import joblib
import matplotlib.pyplot as plt
import pandas as pd

from . import config as C
from .viz import trip_map

df = pd.read_parquet(C.PROC / "points.parquet")
try:
    G, edges, epsg = joblib.load(C.PROC / "network.joblib")
except Exception:
    edges = None
out = C.RES / "label_aids"
out.mkdir(exist_ok=True)
for tid, d in df.groupby("trip"):
    d = d.reset_index(drop=True)
    trip_map(d, None, edges, label_every=25).save(out / f"{tid}_map.html")
    fig, ax = plt.subplots(2, 1, figsize=(11, 5), sharex=True)
    ax[0].plot(d["idx"], d["speed_calc"] * 3.6, lw=1)
    ax[0].set_ylabel("speed (km/h)")
    ax[1].plot(d["idx"], d["height"], lw=1)
    ax[1].set_ylabel("height (m)")
    ax[1].set_xlabel("point number (idx)")
    for a in ax:
        a.grid(alpha=0.4)
        a.set_xticks(range(0, int(d["idx"].max()) + 1, 50))
        a.tick_params(labelsize=7)
    fig.suptitle(tid)
    fig.tight_layout()
    fig.savefig(out / f"{tid}_plot.png", dpi=110)
    plt.close(fig)
print("written to", out)