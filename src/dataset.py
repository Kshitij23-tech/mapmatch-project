from .candidates import build_index, candidates_for_points
from .preprocess import derive_kinematics


def _features(d, cands, grp):
    from .features import trip_features      # imported here because features.py is written on Day 6
    return trip_features(d, cands, grp)


def prepare(df, edges, with_features=True):
    """Turn a points table (columns trip, t, x, y and optionally label) into a list of per-trip dicts."""
    tree, geoms = build_index(edges)
    grp = edges["grp"].to_numpy()
    trips = []
    for tid, d in df.groupby("trip", sort=False):
        d = derive_kinematics(d.reset_index(drop=True))
        xy = d[["x", "y"]].to_numpy()
        cands = candidates_for_points(xy, tree, geoms)
        trips.append({"trip": tid, "xy": xy, "cands": cands, "df": d,
                      "feats": _features(d, cands, grp) if with_features else None,
                      "label": d["label"].to_numpy() if "label" in d else None})
    return trips