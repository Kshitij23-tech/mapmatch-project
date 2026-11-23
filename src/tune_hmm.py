import itertools

import joblib
import numpy as np
import pandas as pd

from . import config as C
from .dataset import prepare
from .evaluate import group_pred, main_distance, metrics
from .hmm_matcher import viterbi
from .network import Network
from .labels import attach

df = attach(pd.read_parquet(C.PROC / "points.parquet"))
df = df[df["label"] >= 0]
G, edges, epsg = joblib.load(C.PROC / "network.joblib")
net = Network(G, edges)
trips = prepare(df, edges, with_features=False)

rows = []
for sigma, beta in itertools.product([5, 10, 15, 20], [5, 10, 20, 40]):
    ys, ps, err = [], [], []
    for t in trips:
        p = group_pred(viterbi(t["xy"], t["cands"], net, sigma=sigma, beta=beta), net.grp)
        ys.append(t["label"])
        ps.append(p)
        err.append(abs(main_distance(t["xy"], p) - main_distance(t["xy"], t["label"])))
    rows.append({"sigma": sigma, "beta": beta, "accuracy": metrics(np.concatenate(ys), np.concatenate(ps))["acc"],
                 "mean_distance_error_m": float(np.mean(err))})
    print(rows[-1], flush=True)
res = pd.DataFrame(rows).sort_values(["accuracy", "mean_distance_error_m"], ascending=[False, True])
res.to_csv(C.RES / "hmm_tuning.csv", index=False)
print("\nbest settings first:")
print(res.round(3).to_string(index=False))
b = res.iloc[0]
print(f"\nPut these in src/config.py:  SIGMA_M = {b.sigma:g}   BETA_M = {b.beta:g}")