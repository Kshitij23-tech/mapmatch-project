import sys

import joblib
import numpy as np
import pandas as pd
from shapely import STRtree, points

from . import config as C
from .labels import attach, read_segments

trip = sys.argv[1] if len(sys.argv) > 1 else "Dataset4"
df = attach(pd.read_parquet(C.PROC / "points.parquet"))
G, edges, epsg = joblib.load(C.PROC / "network.joblib")
tree = STRtree(edges.geometry.values)
d = df[df["trip"] == trip].sort_values("idx").reset_index(drop=True)
pair, dist = tree.query_nearest(points(d["x"].to_numpy(), d["y"].to_numpy()), return_distance=True, all_matches=False)
order = np.argsort(pair[0])
e = edges.iloc[pair[1][order]].reset_index(drop=True)
d["hw"], d["name"], d["grp"], d["dist_m"] = e["hw"], e["name"].astype(str).str[:30], e["grp"], dist[order]
seg = read_segments()
for _, s in seg[seg["trip"] == trip].iterrows():
    x = d[(d["idx"] >= s.start_idx) & (d["idx"] <= s.end_idx)]
    print(f"\n--- points {s.start_idx} to {s.end_idx}, your label: {'main road' if s.label == 0 else 'service road' if s.label == 1 else 'other'}")
    t = x.groupby(["hw", "name", "grp"]).agg(points=("idx", "size"), median_dist_m=("dist_m", "median"),
                                            first=("idx", "min"), last=("idx", "max")).reset_index().sort_values("points", ascending=False)
    print(t.head(6).to_string(index=False))