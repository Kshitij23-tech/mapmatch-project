import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from shapely import STRtree, points

from . import config as C

WINDOW = 15            # a point's road is decided by the majority of this many points around it
MIN_RUN = 20           # a stretch shorter than this many points is treated as noise and merged into its neighbours
MAX_DIST = 60.0        # a point further than this (metres) from every road is called "other"

df = pd.read_parquet(C.PROC / "points.parquet")
G, edges, epsg = joblib.load(C.PROC / "network.joblib")
tree = STRtree(edges.geometry.values)
grp = edges["grp"].to_numpy()
out = C.RES / "label_aids"
out.mkdir(parents=True, exist_ok=True)


def runs(x):
    """[(start, end, value)] for a sequence of values."""
    r, s = [], 0
    for i in range(1, len(x) + 1):
        if i == len(x) or x[i] != x[s]:
            r.append([s, i - 1, int(x[s])])
            s = i
    return r


def merge_short(x):
    """Give the shortest stretch (shorter than MIN_RUN) the road of its neighbour, until no short stretch is left."""
    x = x.copy()
    while True:
        r = runs(x)
        short = [k for k, (a, b, v) in enumerate(r) if b - a + 1 < MIN_RUN]
        if not short or len(r) == 1:
            return x
        k = min(short, key=lambda k: r[k][1] - r[k][0])
        a, b, v = r[k]
        left = r[k - 1][2] if k > 0 else None
        right = r[k + 1][2] if k + 1 < len(r) else None
        x[a:b + 1] = left if left is not None else right


rows = []
for tid, d in df.groupby("trip"):
    d = d.sort_values("idx").reset_index(drop=True)
    pts = points(d["x"].to_numpy(), d["y"].to_numpy())
    pair, dist = tree.query_nearest(pts, return_distance=True, all_matches=False)
    order = np.argsort(pair[0])
    ti, dd = pair[1][order], dist[order]
    g = np.where(dd <= MAX_DIST, grp[ti], 2)
    v = pd.Series(np.where(g == 1, 1.0, np.where(g == 0, 0.0, np.nan)))
    frac = v.rolling(WINDOW, center=True, min_periods=1).mean().ffill().bfill().fillna(0.5)
    smooth = (frac > 0.5).astype(int).to_numpy()
    smooth = merge_short(smooth)
    segs = runs(smooth)
    print(f"\n=== {tid}: {len(d)} points")
    raw01 = g[(g == 0) | (g == 1)]
    print(f"    {100 * np.mean(raw01 == 0):.0f}% of the points are nearest to a main road, {100 * np.mean(raw01 == 1):.0f}% to a service road")
    for a, b, lab in segs:
        agree = 100 * np.mean(g[a:b + 1] == lab)
        word = "main road" if lab == 0 else "service road"
        print(f"    points {d['idx'][a]:>4} to {d['idx'][b]:>4}  ({b - a + 1:>3} points, about {int(d['idx'][a]) // 60}:{int(d['idx'][a]) % 60:02d} to {int(d['idx'][b]) // 60}:{int(d['idx'][b]) % 60:02d} min:s)  looks like {word}  (nearest road agrees for {agree:.0f}%)")
        rows.append({"trip": tid, "start_idx": int(d["idx"][a]), "end_idx": int(d["idx"][b]), "label": lab, "note": "SUGGESTED: confirm in the video"})
    for (a1, b1, l1), (a2, b2, l2) in zip(segs[:-1], segs[1:]):
        print(f"    -> change at point {d['idx'][a2]} (about {int(d['idx'][a2]) // 60}:{int(d['idx'][a2]) % 60:02d} into the recording): "
              f"{'main road' if l1 == 0 else 'service road'} -> {'main road' if l2 == 0 else 'service road'}   CHECK THIS MOMENT IN THE VIDEO")
    fig, ax = plt.subplots(figsize=(11, 3))
    ax.scatter(d["idx"], np.where(g == 2, np.nan, g), s=6, color="#9ca3af", label="nearest road, point by point")
    ax.plot(d["idx"], smooth, color="#e08a00", lw=2, label="suggested (smoothed)")
    for a, b, l in segs[1:]:
        ax.axvline(d["idx"][a], color="#b00020", ls="--", lw=1)
    ax.set_yticks([0, 1])
    ax.set_yticklabels(["main road", "service road"])
    ax.set_xticks(range(0, int(d["idx"].max()) + 1, 50))
    ax.tick_params(labelsize=7)
    ax.set_xlabel("point number (idx)")
    ax.grid(alpha=0.3)
    ax.legend(fontsize=7, loc="center right")
    ax.set_title(f"{tid}: red dashed lines = suggested road changes")
    fig.tight_layout()
    fig.savefig(out / f"{tid}_suggest.png", dpi=110)
    plt.close(fig)

pd.DataFrame(rows).to_csv(out / "suggested_labels.csv", index=False)
print("\nsaved results/label_aids/suggested_labels.csv and one *_suggest.png picture per dataset")