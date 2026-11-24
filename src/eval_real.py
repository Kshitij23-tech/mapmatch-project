import joblib
import numpy as np
import pandas as pd

from . import config as C
from .baseline import nearest
from .dataset import prepare
from .evaluate import confusion, group_pred, main_distance, metrics, switch_scores
from .network import Network
from .labels import attach

METHODS = ["nearest", "hmm", "ml", "hybrid"]
EXTRA = []

NEED_FEATURES = any(m in METHODS + EXTRA for m in ["ml", "hybrid", "ml_real", "hybrid_real"])


def main():
    df = pd.read_parquet(C.PROC / "points.parquet")
    G, edges, epsg = joblib.load(C.PROC / "network.joblib")
    net = Network(G, edges)
    d = attach(df)
    d = d[d["label"] >= 0]
    trips = prepare(d, edges, with_features=NEED_FEATURES)
    if NEED_FEATURES:
        from .classifier import fit, p_service
        from .features import FEATURES
        saved = joblib.load(C.PROC / "model.joblib")


    preds = {}                                   # method -> list of predicted group arrays (one per trip)
    for k, t in enumerate(trips):
        t_preds = {}
        for m in METHODS + EXTRA:
            if m == "nearest":
                t_preds[m] = group_pred(nearest(t["cands"]), net.grp)
            elif m == "hmm":
                from .hmm_matcher import viterbi
                t_preds[m] = group_pred(viterbi(t["xy"], t["cands"], net), net.grp)
            elif m == "ml":
                t_preds[m] = (p_service(saved["model"], t["feats"], FEATURES) > 0.5).astype(int)
            elif m == "hybrid":
                from .fuse import make_bias
                from .hmm_matcher import viterbi
                p = p_service(saved["model"], t["feats"], FEATURES)
                bias = make_bias(p, t["cands"], net.grp, saved["w"])
                t_preds[m] = group_pred(viterbi(t["xy"], t["cands"], net, bias=bias), net.grp)
            elif m in ("ml_real", "hybrid_real"):
                from .fuse import make_bias
                from .hmm_matcher import viterbi
                others = [o for j, o in enumerate(trips) if j != k]
                model = fit(others, FEATURES)               # trained on the other four datasets only
                p = p_service(model, t["feats"], FEATURES)
                if m == "ml_real":
                    t_preds[m] = (p > 0.5).astype(int)
                else:
                    bias = make_bias(p, t["cands"], net.grp, saved["w"])
                    t_preds[m] = group_pred(viterbi(t["xy"], t["cands"], net, bias=bias), net.grp)
        for m, v in t_preds.items():
            preds.setdefault(m, []).append(v)
        print("done", t["trip"], flush=True)

    rows, pooled, out_pts = [], [], []
    for m in METHODS + EXTRA:
        ys, ps = [], []
        for t, p in zip(trips, preds[m]):
            y = t["label"]
            r = metrics(y, p)
            ref = main_distance(t["xy"], y)
            got = main_distance(t["xy"], p)
            sw = switch_scores(y, p)
            rows.append({"method": m, "trip": t["trip"], "acc": r["acc"], "points": r["n"], "ref_main_m": ref, "pred_main_m": got,
                         "dist_err_m": abs(got - ref), "dist_err_%": 100 * abs(got - ref) / ref if ref > 0 else np.nan, **sw})
            ys.append(y)
            ps.append(p)
            out_pts.append(pd.DataFrame({"method": m, "trip": t["trip"], "idx": t["df"]["idx"].to_numpy(), "true": y, "pred": p}))
        pooled.append({"method": m, **metrics(np.concatenate(ys), np.concatenate(ps))})
    by_trip = pd.DataFrame(rows)
    pooled = pd.DataFrame(pooled)
    by_trip.to_csv(C.RES / "real_by_trip.csv", index=False)
    pooled.to_csv(C.RES / "real_pooled.csv", index=False)
    pd.concat(out_pts).to_parquet(C.RES / "real_preds.parquet", index=False)

    pd.options.display.float_format = "{:.2f}".format
    print("\nAccuracy per dataset (share of scored points with the right road):")
    print(by_trip.pivot(index="trip", columns="method", values="acc").reindex(columns=METHODS + EXTRA).to_string())
    print("\nDistance on the main road in metres (reference first):")
    ref = by_trip.drop_duplicates("trip").set_index("trip")["ref_main_m"].round(0).rename("reference")
    dist = by_trip.pivot(index="trip", columns="method", values="pred_main_m").round(0)
    print(pd.concat([ref, dist.reindex(columns=METHODS + EXTRA)], axis=1).to_string())
    print("\nError of that distance in metres (percent of the reference is in real_by_trip.csv):")
    print(by_trip.pivot(index="trip", columns="method", values="dist_err_m").reindex(columns=METHODS + EXTRA).round(0).to_string())
    print("\nRoad changes found within 5 s (found / true / extra predicted):")
    sw = by_trip.assign(s=lambda x: x["switch_found"].astype(str) + "/" + x["switch_true"].astype(str) + "/" + x["switch_extra"].astype(str))
    print(sw.pivot(index="trip", columns="method", values="s").reindex(columns=METHODS + EXTRA).to_string())
    print("\nAll datasets together:")
    print(pooled.round(3).to_string(index=False))
    print("\nsaved results/real_by_trip.csv, real_pooled.csv, real_preds.parquet")


if __name__ == "__main__":
    main()