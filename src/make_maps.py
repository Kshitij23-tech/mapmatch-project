import joblib
import numpy as np
import pandas as pd

from . import config as C
from .viz import trip_map

pred = pd.read_parquet(C.RES / "real_preds.parquet")
SHOW = ["truth"] + [m for m in ["nearest", "hmm", "hybrid", "leuven"] if m in set(pred["method"])]
FIRST = pred["method"].iloc[0]
pts = pd.read_parquet(C.PROC / "points.parquet").set_index(["trip", "idx"])
G, edges, epsg = joblib.load(C.PROC / "network.joblib")
out = C.RES / "maps"
out.mkdir(exist_ok=True)
links = []
for tid in sorted(pred["trip"].unique()):
    for m in SHOW:
        g = pred[(pred["trip"] == tid) & (pred["method"] == (FIRST if m == "truth" else m))].sort_values("idx")
        d = pts.loc[tid].loc[g["idx"]].reset_index()
        code = g["true" if m == "truth" else "pred"].to_numpy()
        trip_map(d, np.where(code < 0, -1, code), edges, label_every=50).save(out / f"{tid}_{m}.html")
        links.append(f'<li><a href="{tid}_{m}.html">{tid} - {m}</a></li>')
(out / "index.html").write_text("<h2>Result maps</h2><p>amber = main road, teal = service road, grey = other road, black = no match</p><ul>" + "".join(links) + "</ul>")
print("open results/maps/index.html in your browser")