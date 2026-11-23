import joblib
import numpy as np
import pandas as pd
from shapely import STRtree, points

from . import config as C
from .labels import attach

df = attach(pd.read_parquet(C.PROC / "points.parquet"))
G, edges, epsg = joblib.load(C.PROC / "network.joblib")
tree = STRtree(edges.geometry.values)
d = df[df["trip"] == "Dataset5"].sort_values("idx").reset_index(drop=True)
pair, dist = tree.query_nearest(points(d["x"].to_numpy(), d["y"].to_numpy()), return_distance=True, all_matches=False)
order = np.argsort(pair[0])
e = edges.iloc[pair[1][order]].reset_index(drop=True)
d["hw"], d["name"], d["ref"], d["bridge"], d["grp"] = e["hw"], e["name"].astype(str).str[:30], e["ref"].astype(str).str[:12], e["bridge"], e["grp"]
d["dist_m"] = dist[order]
d["part"] = pd.cut(d["idx"], [-1, 54, 295, 355], labels=["0-54 (labelled ground road)", "55-295 (labelled flyover)", "296-355 (labelled ground road)"])
t = d.groupby(["part", "hw", "name", "ref", "bridge", "grp"], observed=True).agg(points=("idx", "size"), median_dist_m=("dist_m", "median")).reset_index()
print(t.to_string(index=False))