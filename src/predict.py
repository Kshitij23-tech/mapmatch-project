import sys
from pathlib import Path

import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pyproj import Transformer

from . import config as C
from .classifier import p_service
from .dataset import prepare
from .evaluate import group_pred
from .features import FEATURES
from .fuse import make_bias
from .hmm_matcher import Network, viterbi
from .preprocess import drop_jumps

NAMES = {0: "main", 1: "service", 2: "other", -1: "unknown"}
COL = {0: "#e08a00", 1: "#0d8f8f", 2: "#6b7280", -1: "#000000"}


def read_trip(path):
    d = pd.read_csv(path)
    d.columns = [c.strip().lower() for c in d.columns]
    for need in ["lat", "lon"]:
        if need not in d.columns:
            raise SystemExit(f"Input needs a column named '{need}'. Found: {d.columns.tolist()}")
    tcol = "time" if "time" in d.columns else ("t" if "t" in d.columns else None)
    if tcol is None:
        d["t"] = np.arange(len(d), dtype=float)          # no time column: assume 1 reading per second
    elif pd.api.types.is_numeric_dtype(d[tcol]):
        d["t"] = d[tcol].astype(float)                   # numbers are taken as seconds
    else:
        tt = pd.to_datetime(d[tcol], errors="coerce")
        d["t"] = (tt - tt.min()).dt.total_seconds()
    d = d.dropna(subset=["lat", "lon", "t"]).sort_values("t").drop_duplicates("t")
    d["trip"] = Path(path).stem
    return d[["trip", "t", "lat", "lon"]].reset_index(drop=True)


def main():
    if len(sys.argv) < 2:
        raise SystemExit("Usage: python -m src.predict path/to/trip.csv")
    src = Path(sys.argv[1])
    d = read_trip(src)

    G, edges, epsg = joblib.load(C.PROC / "network.joblib")
    net = Network(G, edges)
    saved = joblib.load(C.PROC / "model.joblib")

    tr = Transformer.from_crs(4326, epsg, always_xy=True)
    d["x"], d["y"] = tr.transform(d["lon"].to_numpy(), d["lat"].to_numpy())
    d = drop_jumps(d)
    if len(d) < C.MIN_POINTS:
        raise SystemExit(f"Only {len(d)} usable points; need at least {C.MIN_POINTS}.")

    t = prepare(d, edges)[0]
    p = p_service(saved["model"], t["feats"], FEATURES)
    bias = make_bias(p, t["cands"], net.grp, saved["w"])
    groups = group_pred(viterbi(t["xy"], t["cands"], net, bias=bias), net.grp)

    out = t["df"][["t", "lat", "lon"]].copy()
    out["road"] = [NAMES[int(g)] for g in groups]
    out["p_service"] = p.round(3)
    out_csv = src.with_name(src.stem + "_labelled.csv")
    out.to_csv(out_csv, index=False)

    xy = t["xy"]
    fig, ax = plt.subplots(figsize=(8, 8))
    for g, c in COL.items():
        e = edges[edges["grp"] == g]
        if len(e):
            e.plot(ax=ax, color=c, linewidth=1, alpha=0.35)
    for g, c in COL.items():
        m = groups == g
        if m.any():
            ax.scatter(xy[m, 0], xy[m, 1], s=8, color=c, label=NAMES[g], zorder=3)
    pad = 150
    ax.set_xlim(xy[:, 0].min() - pad, xy[:, 0].max() + pad)
    ax.set_ylim(xy[:, 1].min() - pad, xy[:, 1].max() + pad)
    ax.set_aspect("equal")
    ax.legend()
    ax.set_title(src.stem + " - road type per point")
    out_png = src.with_name(src.stem + "_labelled.png")
    fig.savefig(out_png, dpi=130, bbox_inches="tight")

    share = out["road"].value_counts(normalize=True).round(2).to_dict()
    print("points labelled:", len(out), " share:", share)
    print("saved", out_csv)
    print("saved", out_png)


if __name__ == "__main__":
    main()