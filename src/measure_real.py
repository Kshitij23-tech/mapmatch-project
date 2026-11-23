"""Measures your real data so the simulator can copy it. Run after the labels are done."""
import joblib
import numpy as np
import pandas as pd

from . import config as C
from .candidates import build_index, candidates_for_points
from .labels import attach

df = attach(pd.read_parquet(C.PROC / "points.parquet"))
G, edges, epsg = joblib.load(C.PROC / "network.joblib")
tree, geoms = build_index(edges)
grp = edges["grp"].to_numpy()


def nearest_of(xy, group):
    """Distance from every point to the nearest road of one group (60 m if none is that close)."""
    out = np.full(len(xy), C.SEARCH_RADIUS_M)
    for i, cl in enumerate(candidates_for_points(xy, tree, geoms, k=C.MAX_CANDS)):
        d = [c[1] for c in cl if grp[c[0]] == group]
        if d:
            out[i] = min(d)
    return out


own, other = [], []
for lab in (0, 1):
    d = df[df["label"] == lab]
    xy = d[["x", "y"]].to_numpy()
    own.append(nearest_of(xy, lab))
    other.append(nearest_of(xy, 1 - lab))
sigma = float(np.median(np.concatenate(own)) / 0.6745)      # median of |normal error| is 0.6745 sigma
gap = float(np.median(other[1]))                             # service-road points: distance to the nearest main road
print(f"GPS error: points sit a median of {np.median(np.concatenate(own)):.1f} m from the road they are on  ->  sigma about {sigma:.1f} m")
print(f"Gap: service-road points are a median of {gap:.1f} m from the nearest main road")

rows = []
for lab, name in ((0, "main road"), (1, "service road")):
    s = df[df["label"] == lab]["speed_calc"]
    rows.append({"road": name, "points": len(s), "mean_m_s": s.mean(), "mean_km_h": s.mean() * 3.6, "std_m_s": s.std(),
                 "share_below_1_m_s_%": 100 * (s < 1).mean()})
print()
print(pd.DataFrame(rows).round(1).to_string(index=False))
v_hw, v_sr = rows[0]["mean_m_s"], rows[1]["mean_m_s"]
stop = rows[1]["share_below_1_m_s_%"] / 100
print("\nPut these in src/config.py (replace the lines in the 'Simulator' block):")
print(f"SIM_GAP_M = {gap:.0f}.0")
print(f"SIM_SIGMA_M = {min(max(sigma, 2.0), 15.0):.1f}")
print(f"V_HW = {v_hw:.1f}")
print(f"V_SR = {v_sr:.1f}")
print(f"SIM_STOP_P = {min(max(stop / 6, 0.0), 0.02):.3f}")