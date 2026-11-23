import joblib
import networkx as nx
import pandas as pd
from shapely.geometry import Point
from shapely import STRtree

from . import config as C
from .labels import attach

df = attach(pd.read_parquet(C.PROC / "points.parquet"))
G, edges, epsg = joblib.load(C.PROC / "network.joblib")
tree = STRtree(edges.geometry.values)
# (dataset, first point of the new road, road before, road after)  0 = main road, 1 = service road
CHANGES = [("Dataset3", 93, 1, 0), ("Dataset3", 523, 0, 1), ("Dataset4", 388, 0, 1), ("Dataset4", 829, 1, 0)]


def edge_of(trip, idx, grp):
    r = df[(df["trip"] == trip) & (df["idx"] == idx)].iloc[0]
    p = Point(r["x"], r["y"])
    cand = [i for i in tree.query(p.buffer(80)) if edges["grp"].iat[i] == grp]
    return (min(cand, key=lambda i: edges.geometry.iat[i].distance(p)), p) if cand else (None, p)


for trip, idx, g_from, g_to in CHANGES:
    e1, p1 = edge_of(trip, idx - 25, g_from)
    e2, p2 = edge_of(trip, idx + 25, g_to)
    word = lambda g: "main" if g == 0 else "service"
    print(f"\n{trip}, change at point {idx}: {word(g_from)} -> {word(g_to)}")
    if e1 is None or e2 is None:
        print("   no road of that type within 80 m of the point before or after the change")
        continue
    a, b = edges.iloc[e1], edges.iloc[e2]
    print(f"   before: {a['hw']} {str(a['name'])[:28]}   after: {b['hw']} {str(b['name'])[:28]}   straight line {p1.distance(p2):.0f} m")
    try:
        n = nx.shortest_path_length(G, a["v"], b["u"], weight="length")
        print(f"   route exists: {n:.0f} m")
    except nx.NetworkXNoPath:
        print("   NO ROUTE between these two roads in the downloaded map")