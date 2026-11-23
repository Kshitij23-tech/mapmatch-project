import json

import geopandas as gpd
import joblib
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import osmnx as ox
import pandas as pd
from shapely import unary_union
from shapely.geometry import LineString

from . import config as C
from .candidates import build_index, candidates_for_points
from .viz import roads_map

ox.settings.cache_folder = str(C.ROOT / "cache")     # downloads are saved here, so a second run is instant
ox.settings.requests_timeout = 300

COLOR = {0: "#e08a00", 1: "#0d8f8f", 2: "#9ca3af"}   # main road, service road, everything else


def first(v):
    return v[0] if isinstance(v, list) else v


def text_of(v):
    if isinstance(v, list):
        v = " ".join(map(str, v))
    return "" if v is None or (isinstance(v, float) and np.isnan(v)) else str(v)


def group_of(row):
    """0 = main road, 1 = service road, 2 = anything else. Names and refs win over tags."""
    words = (text_of(row.get("name")) + " " + text_of(row.get("ref"))).lower()
    if any(w.lower() in words for w in C.SERVICE_WORDS):
        return 1
    if any(w.lower() in words for w in C.MAIN_WORDS):
        return 0
    if row["hw"] in C.MAIN_TAGS:
        return 0
    if row["hw"] in C.SERVICE_TAGS:
        return 1
    return 2


def study_polygon(df, epsg, buffer_m=250.0):
    """Area to download: a strip of buffer_m metres around every dataset."""
    lines = [LineString(d[["x", "y"]].to_numpy()) for _, d in df.groupby("trip") if len(d) > 1]
    area = unary_union(gpd.GeoSeries(lines, crs=epsg).buffer(buffer_m).tolist()).simplify(30)
    return gpd.GeoSeries([area], crs=epsg).to_crs(4326).iloc[0]


def download(poly):
    parts = list(poly.geoms) if poly.geom_type == "MultiPolygon" else [poly]
    graphs = []
    for k, p in enumerate(parts, 1):
        print(f"downloading area {k} of {len(parts)} ...", flush=True)
        graphs.append(ox.graph_from_polygon(p, network_type="drive_service", retain_all=True))
    return nx.compose_all(graphs)


def build_network(G, epsg):
    edges = ox.graph_to_gdfs(G, nodes=False).reset_index()      # columns u, v, key, geometry, highway, name, ref ...
    for c in ["highway", "name", "ref", "bridge", "layer", "oneway"]:
        if c not in edges:
            edges[c] = None
    edges["hw"] = edges["highway"].map(first)
    edges["grp"] = edges.apply(group_of, axis=1)
    edges["bridge"] = edges["bridge"].map(lambda v: text_of(v) not in ("", "no", "nan", "None"))
    return edges.to_crs(epsg)

def apply_area_rules(edges, df):
    """Some places name the roads differently from the rest of the area. Roads near the dataset named in a rule get their group from the words of that rule."""
    for rule in C.AREA_RULES:
        d = df[df["trip"] == rule["trip"]]
        if d.empty:
            continue
        zone = LineString(d[["x", "y"]].to_numpy()).buffer(rule.get("buffer_m", 300.0))
        changed = 0
        for i in edges.index[edges.intersects(zone)]:
            words = (text_of(edges.at[i, "name"]) + " " + text_of(edges.at[i, "ref"])).lower()
            new = 1 if any(w.lower() in words for w in rule["service_words"]) else 0 if any(w.lower() in words for w in rule["main_words"]) else None
            if new is not None and new != edges.at[i, "grp"]:
                edges.at[i, "grp"] = new
                changed += 1
        print(f"area rule for {rule['trip']}: {changed} roads changed group")
    return edges

def nearest_table(df, edges, radius=40.0):
    """For every dataset: which kind of road is each point nearest to? (the table you read on Day 1)"""
    tree, geoms = build_index(edges)
    rows = []
    for tid, d in df.groupby("trip"):
        c = candidates_for_points(d[["x", "y"]].to_numpy(), tree, geoms, radius=radius, k=1)
        for cl in c:
            if cl:
                e = edges.iloc[cl[0][0]]
                rows.append({"trip": tid, "hw": e["hw"], "name": text_of(e["name"])[:28], "ref": text_of(e["ref"])[:12],
                             "bridge": bool(e["bridge"]), "grp": int(e["grp"])})
            else:
                rows.append({"trip": tid, "hw": "none within %d m" % radius, "name": "", "ref": "", "bridge": False, "grp": -1})
    t = pd.DataFrame(rows)
    n = t.groupby("trip").size()
    out = t.groupby(["trip", "hw", "name", "ref", "bridge", "grp"]).size().rename("points").reset_index()
    out["share_%"] = (100 * out["points"] / out["trip"].map(n)).round(0).astype(int)
    return out.sort_values(["trip", "points"], ascending=[True, False])


if __name__ == "__main__":
    df = pd.read_parquet(C.PROC / "points.parquet")
    epsg = json.loads((C.PROC / "meta.json").read_text())["epsg"]
    poly = study_polygon(df, epsg)
    G = download(poly)
    edges = build_network(G, epsg)
    edges = apply_area_rules(edges, df)
    print("\nroad types in the download (hw = OpenStreetMap highway tag, grp: 0 main, 1 service, 2 other):")
    print(edges.groupby(["hw", "grp"]).size().to_string())
    joblib.dump((G, edges, epsg), C.PROC / "network.joblib")

    tab = nearest_table(df, edges)
    print("\nnearest road of every GPS point (within 40 m), per dataset:")
    print(tab.groupby("trip").head(6).to_string(index=False))

    print("\nsanity check with the datasets you know:")
    tree, geoms = build_index(edges)
    for tid, want in C.TRIP_KNOWN.items():
        d = df[df["trip"] == tid]
        c = candidates_for_points(d[["x", "y"]].to_numpy(), tree, geoms, radius=40, k=1)
        share = np.mean([bool(cl) and edges["grp"].iloc[cl[0][0]] == want for cl in c])
        word = "main road" if want == 0 else "service road"
        flag = "OK" if share >= 0.7 else "TOO LOW: change MAIN_TAGS / SERVICE_TAGS / words in src/config.py"
        print(f"  {tid} should be on the {word}: {100 * share:.0f}% of its points are nearest to a {word} edge  -> {flag}")

    fig, ax = plt.subplots(figsize=(9, 9))
    for g, col in COLOR.items():
        edges[edges["grp"] == g].plot(ax=ax, color=col, linewidth=2)
    ax.scatter(df["x"][::5], df["y"][::5], s=2, c="#14213d")
    ax.set_aspect("equal")
    fig.savefig(C.RES / "network.png", dpi=150)
    roads_map(edges, df).save(C.RES / "roads_map.html")
    print("\nsaved results/network.png and results/roads_map.html")