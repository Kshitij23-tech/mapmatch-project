import geopandas as gpd
import networkx as nx
import numpy as np
import pandas as pd
from shapely.geometry import LineString

from . import config as C

LENGTH = 4000.0                         # corridor length (metres)
JUNCTIONS = (1300.0, 2700.0)            # where connectors join the two roads
HW_NAME = {0: "trunk", 1: "service", 2: "residential"}


def corridor(gap):
    """A main road (y = 0) and a parallel service road (y = gap), joined by connectors at the two junctions."""
    xs = [0.0, *JUNCTIONS, LENGTH]
    xy = {f"{r}{i}": (x, 0.0 if r == "H" else gap) for r in "HS" for i, x in enumerate(xs)}
    links = []
    for r, grp in (("H", 0), ("S", 1)):
        for i in range(len(xs) - 1):
            links.append((f"{r}{i}", f"{r}{i + 1}", grp))
    for i in (1, 2):
        links += [(f"H{i}", f"S{i}", 2), (f"S{i}", f"H{i}", 2)]
    G, rows = nx.MultiDiGraph(), []
    for u, v, grp in links:
        geom = LineString([xy[u], xy[v]])
        G.add_edge(u, v, key=0, length=geom.length)
        rows.append({"u": u, "v": v, "key": 0, "grp": grp, "hw": HW_NAME[grp], "name": "", "ref": "", "bridge": False, "geometry": geom})
    return G, gpd.GeoDataFrame(rows, geometry="geometry")


def path_for(kind, gap, rng):
    """kind is a string of road letters, e.g. 'H', 'S', 'HS', 'SH', 'HSH', 'SHS'. Returns the path and the road type of each piece."""
    pts, modes = [(0.0, 0.0 if kind[0] == "H" else gap)], []
    if len(kind) == 1:
        pts.append((LENGTH, pts[0][1]))
        return np.array(pts), [0 if kind == "H" else 1]
    if len(kind) == 2:
        js = [JUNCTIONS[int(rng.integers(0, 2))]]
    else:
        js = list(JUNCTIONS)
    cur = kind[0]
    for j, nxt in zip(js, kind[1:]):
        y_cur, y_nxt = (0.0 if cur == "H" else gap), (0.0 if nxt == "H" else gap)
        pts += [(j, y_cur), (j, y_nxt)]
        modes += [0 if cur == "H" else 1, 2]
        cur = nxt
    pts.append((LENGTH, 0.0 if cur == "H" else gap))
    modes.append(0 if cur == "H" else 1)
    return np.array(pts), modes


def ar1(rng, n, sigma, rho=0.95):
    """Slowly drifting GPS error, like real receivers (not independent from second to second)."""
    e = np.empty(n)
    e[0] = rng.normal(0, sigma)
    k = sigma * np.sqrt(1 - rho ** 2)
    for i in range(1, n):
        e[i] = rho * e[i - 1] + rng.normal(0, k)
    return e


def simulate_trip(rng, tid, kind, gap, sigma, v_hw, v_sr, stop_p):
    pts, modes = path_for(kind, gap, rng)
    cum = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(pts, axis=0).T))])
    speeds = {0: v_hw, 1: v_sr, 2: 6.0}
    s, v, stop_left = 0.0, speeds[modes[0]], 0
    S, M = [], []
    while s < cum[-1] and len(S) < 3000:
        piece = min(int(np.searchsorted(cum, s, side="right")) - 1, len(modes) - 1)
        mode = modes[piece]
        target = speeds[mode]
        if mode == 1:                                   # service road: occasional stops
            if stop_left > 0:
                target, stop_left = 0.0, stop_left - 1
            elif rng.random() < stop_p:
                stop_left = int(rng.integers(3, 12))
        v = max(0.0, v + 0.25 * (target - v) + rng.normal(0, 0.12 * max(target, 1.0)))
        S.append(s)
        M.append(mode)
        s += v
    S, M = np.array(S), np.array(M)
    n = len(S)
    x = np.interp(S, cum, pts[:, 0]) + ar1(rng, n, sigma)
    y = np.interp(S, cum, pts[:, 1]) + ar1(rng, n, sigma)
    t = np.arange(n, dtype=float)
    return pd.DataFrame({"trip": tid, "idx": np.arange(n), "t": t, "x": x, "y": y, "label": M, "kind": kind})


def make_trips(rng, n, tag, gap=None, sigma=None, v_hw=None, v_sr=None, stop_p=None):
    gap = C.SIM_GAP_M if gap is None else gap
    sigma = C.SIM_SIGMA_M if sigma is None else sigma
    v_hw = C.V_HW if v_hw is None else v_hw
    v_sr = C.V_SR if v_sr is None else v_sr
    stop_p = C.SIM_STOP_P if stop_p is None else stop_p
    kinds = rng.choice(["H", "S", "HS", "SH", "HSH", "SHS"], size=n)
    return pd.concat([simulate_trip(rng, f"{tag}_{i}", k, gap, sigma, v_hw, v_sr, stop_p) for i, k in enumerate(kinds)],
                     ignore_index=True)