"""Where do the methods go wrong? Lists runs of wrong points and whether they sit next to a road change."""
import joblib
import numpy as np
import pandas as pd

from . import config as C
from .evaluate import switches
from .viz import trip_map

SHOW = ["nearest", "hmm", "hybrid"]
NEAR = 10                                    # a wrong run within this many points of a true road change is called "near a change"

pred = pd.read_parquet(C.RES / "real_preds.parquet")
pts = pd.read_parquet(C.PROC / "points.parquet").set_index(["trip", "idx"])
G, edges, epsg = joblib.load(C.PROC / "network.joblib")
out = C.RES / "failure_maps"
out.mkdir(exist_ok=True)

rows = []
for m in SHOW:
    for tid, g in pred[pred["method"] == m].groupby("trip"):
        g = g.sort_values("idx").reset_index(drop=True)
        true = g["true"].to_numpy()
        ok = np.isin(true, [0, 1])
        wrong = ok & (g["pred"].to_numpy() != true)
        sw = [p for p, _ in switches(true)]
        i = 0
        while i < len(g):
            if not wrong[i]:
                i += 1
                continue
            j = i
            while j + 1 < len(g) and wrong[j + 1]:
                j += 1
            near = min((abs(k - s) for s in sw for k in (i, j)), default=999)
            rows.append({"method": m, "trip": tid, "from_idx": int(g["idx"][i]), "to_idx": int(g["idx"][j]), "points": j - i + 1,
                         "true": int(true[i]), "predicted": int(g["pred"][i]),
                         "distance_to_road_change": near if near < 999 else None,
                         "speed_m_s": round(float(pts.loc[[(tid, k) for k in g["idx"][i:j + 1]], "speed_calc"].mean()), 1),
                         "where": "near a road change" if near <= NEAR else "far from a road change"})
            i = j + 1
runs = pd.DataFrame(rows)
runs.to_csv(C.RES / "failures.csv", index=False)
if runs.empty:
    print("No wrong runs at all for", SHOW)
else:
    pd.options.display.width = 160
    print("wrong points by method and where they are:")
    print(runs.pivot_table(index="method", columns="where", values="points", aggfunc="sum", fill_value=0).to_string())
    print("\nthe 12 longest wrong runs of the last method in SHOW:")
    last = runs[runs["method"] == SHOW[-1]].sort_values("points", ascending=False).head(12)
    print(last.to_string(index=False) if len(last) else "none")

for tid, g in pred[pred["method"] == SHOW[-1]].groupby("trip"):
    g = g.sort_values("idx").reset_index(drop=True)
    d = pts.loc[tid].loc[g["idx"]].reset_index()
    code = np.where(np.isin(g["true"], [0, 1]) & (g["pred"] != g["true"]), -1, g["pred"].clip(0, 2))
    trip_map(d, code, edges, label_every=50).save(out / f"{tid}.html")
print(f"\nmaps with the wrong points in black: {out}")