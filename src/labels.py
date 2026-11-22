"""Ground-truth labels. data/labels.csv lists segments: trip, start_idx, end_idx, label, note.
label: 0 = main road, 1 = service road, 2 = some other road (not scored).  idx = row number in the dataset file, from 0."""
import sys

import joblib
import numpy as np
import pandas as pd

from . import config as C
from .viz import trip_map


def write_template():
    if C.LABELS.exists():
        raise SystemExit(f"{C.LABELS} already exists. Delete it first if you really want a new template.")
    rows = []
    for f in sorted(C.TRIPS.glob("*.csv")):
        n = len(pd.read_csv(f))
        t = f.stem
        if t in C.TRIP_KNOWN:
            rows.append((t, 0, n - 1, C.TRIP_KNOWN[t], "whole dataset on one road type"))
        elif t == "Dataset3":
            rows += [(t, 0, "FILL", 1, "start: service road"), (t, "FILL", "FILL", 0, "main road"),
                     (t, "FILL", n - 1, "FILL", "after the exit: 1 = service road, 2 = other road")]
        elif t == "Dataset4":
            rows += [(t, 0, "FILL", 0, "start: main road"), (t, "FILL", "FILL", 1, "service road"),
                     (t, "FILL", n - 1, 0, "back on the main road")]
        else:
            rows += [(t, 0, n - 1, "FILL", "0 if the vehicle stays on the main road (flyover); split into rows if it changes road")]
    pd.DataFrame(rows, columns=["trip", "start_idx", "end_idx", "label", "note"]).to_csv(C.LABELS, index=False)
    print("written", C.LABELS, "- open it and replace every FILL")


def read_segments():
    seg = pd.read_csv(C.LABELS, dtype=str, keep_default_na=False)
    if (seg[["start_idx", "end_idx", "label"]] == "FILL").any().any() or (seg[["start_idx", "end_idx", "label"]] == "").any().any():
        bad = seg[(seg[["start_idx", "end_idx", "label"]] == "FILL").any(axis=1)]
        raise SystemExit("These rows of data/labels.csv still contain FILL (or are empty):\n" + bad.to_string(index=False))
    for c in ["start_idx", "end_idx", "label"]:
        seg[c] = seg[c].astype(int)
    return seg


def check_segments(seg):
    """Every point of every dataset must be covered by exactly one segment."""
    problems = []
    for f in sorted(C.TRIPS.glob("*.csv")):
        n, t = len(pd.read_csv(f)), f.stem
        s = seg[seg["trip"] == t].sort_values("start_idx")
        if s.empty:
            problems.append(f"{t}: no rows in labels.csv")
            continue
        expect = 0
        for _, r in s.iterrows():
            if r.label not in (0, 1, 2):
                problems.append(f"{t}: label must be 0, 1 or 2 (row starting at {r.start_idx})")
            if r.start_idx != expect:
                problems.append(f"{t}: expected a segment starting at {expect} but found {r.start_idx} "
                                f"({'gap' if r.start_idx > expect else 'overlap'})")
            if r.end_idx < r.start_idx:
                problems.append(f"{t}: end_idx {r.end_idx} is before start_idx {r.start_idx}")
            expect = r.end_idx + 1
        if expect != n:
            problems.append(f"{t}: segments end at {expect - 1} but the file has {n} points (last index {n - 1})")
    if problems:
        raise SystemExit("Fix data/labels.csv:\n  " + "\n  ".join(problems))


def attach(df):
    """Adds an int column 'label' (0, 1, 2) to a points table that has trip and idx. Points without a segment get -1."""
    seg = read_segments()
    df = df.copy()
    df["label"] = -1
    for _, r in seg.iterrows():
        m = (df["trip"] == r.trip) & (df["idx"] >= r.start_idx) & (df["idx"] <= r.end_idx)
        df.loc[m, "label"] = r.label
    return df


def main_distance(xy, lab):
    """Metres travelled with label 0: the straight steps between GPS points, counted when the point reached is on the main road."""
    step = np.hypot(*np.diff(xy, axis=0).T)
    return float(step[np.asarray(lab)[1:] == 0].sum())


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "template":
        write_template()
        return
    seg = read_segments()
    check_segments(seg)
    df = attach(pd.read_parquet(C.PROC / "points.parquet"))
    print("labels.csv is complete. Points per dataset and label:")
    print(pd.crosstab(df["trip"], df["label"]).to_string())
    rows = []
    for tid, d in df.groupby("trip"):
        xy = d[["x", "y"]].to_numpy()
        rows.append({"trip": tid, "total_m": round(float(np.hypot(*np.diff(xy, axis=0).T).sum())),
                     "reference_main_road_m": round(main_distance(xy, d["label"].to_numpy()))})
    ref = pd.DataFrame(rows)
    print("\nreference distance on the main road (this is what the methods are compared with):")
    print(ref.to_string(index=False))
    ref.to_csv(C.RES / "reference_distance.csv", index=False)
    try:
        G, edges, epsg = joblib.load(C.PROC / "network.joblib")
    except Exception:
        edges = None
    out = C.RES / "label_check"
    out.mkdir(exist_ok=True)
    for tid, d in df.groupby("trip"):
        trip_map(d.reset_index(drop=True), d["label"].to_numpy(), edges, label_every=25).save(out / f"{tid}.html")
    print("\nopen the maps in results/label_check: points are amber (main), teal (service), grey (other).")


if __name__ == "__main__":
    main()