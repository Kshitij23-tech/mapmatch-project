"""Dataset5: the vehicle drives on a flyover with a service road below it. Does the height column show the flyover, and do the methods cope?"""
import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from . import config as C
from .candidates import build_index, candidates_for_points
from .hmm_matcher import viterbi
from .network import Network

TRIP = "Dataset5"
RISE_M = 3.0                                 # height above the approach road that counts as "on the flyover"

df = pd.read_parquet(C.PROC / "points.parquet")
d = df[df["trip"] == TRIP].reset_index(drop=True)
h = d["height"].rolling(9, center=True, min_periods=1).median()
base = float(np.median(np.r_[d["height"].iloc[:20], d["height"].iloc[-20:]]))
on = (h > base + RISE_M).to_numpy()
fig, ax = plt.subplots(figsize=(10, 3.5))
ax.plot(d["idx"], d["height"], lw=1, label="height")
ax.axhline(base, color="grey", ls="--", label="height of the approach roads")
ax.fill_between(d["idx"], d["height"].min(), d["height"].max(), where=on, alpha=0.2, color="#e08a00", label=f"more than {RISE_M:g} m above")
ax.set_xlabel("point number (idx)")
ax.set_ylabel("height (m)")
ax.legend(fontsize=8)
fig.tight_layout()
fig.savefig(C.RES / "flyover_height.png", dpi=150)

if not on.any():
    print(f"The height never rises more than {RISE_M:g} m above the approach roads, so the height column does not show a flyover.")
    print("Write that in the report as a limitation. Try RISE_M = 2 at the top of this file if the plot shows a small hump.")
    raise SystemExit
i0, i1 = d["idx"][on].min(), d["idx"][on].max()
print(f"height base {base:.1f} m. Points {i0} to {i1} are more than {RISE_M:g} m above it ({on.sum()} points, peak +{(h.max() - base):.1f} m).")

pred = pd.read_parquet(C.RES / "real_preds.parquet")
pred = pred[pred["trip"] == TRIP].merge(d[["idx"]].assign(on=on), on="idx")
pred = pred[pred["true"].isin([0, 1])]
rows = []
for m, g in pred.groupby("method"):
    rows.append({"method": m, "accuracy_on_flyover": (g[g["on"]]["pred"] == g[g["on"]]["true"]).mean(),
                 "accuracy_elsewhere": (g[~g["on"]]["pred"] == g[~g["on"]]["true"]).mean()})
print("\naccuracy on the flyover part and on the rest of the dataset:")
print(pd.DataFrame(rows).round(3).to_string(index=False))

G, edges, epsg = joblib.load(C.PROC / "network.joblib")
net = Network(G, edges)
tree, geoms = build_index(edges)
xy = d[["x", "y"]].to_numpy()
e = viterbi(xy, candidates_for_points(xy, tree, geoms), net)
ok = (e >= 0) & on
on_bridge = edges["bridge"].to_numpy()[e[ok]]
print(f"\nOn the flyover part the HMM matched {100 * on_bridge.mean():.0f}% of the points to roads that OpenStreetMap marks as bridge.")
print("If that share is high, the flyover is a separate road in the map and the matcher can tell it from the road below.")
print("If it is low, the map has no separate flyover road here and position alone cannot separate the two; say so in the report.")