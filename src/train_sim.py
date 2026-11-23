import itertools

import joblib
import numpy as np
import pandas as pd

from . import config as C
from .baseline import nearest
from .classifier import evaluate_cv, fit, p_service
from .dataset import prepare
from .evaluate import group_pred, metrics
from .features import FEATURES
from .fuse import make_bias
from .hmm_matcher import viterbi
from .network import Network
from .simulator import corridor, make_trips

rng = np.random.default_rng(0)
# Several conditions around the numbers measured on your data, so the classifier and the weight do not depend on one guess
CONDITIONS = [(g * C.SIM_GAP_M, s * C.SIM_SIGMA_M) for g, s in itertools.product([0.5, 1.0, 1.5], [1.0, 2.0])]
print(f"measured: gap {C.SIM_GAP_M} m, GPS error {C.SIM_SIGMA_M} m, speeds {C.V_HW} (main) and {C.V_SR} (service) m/s")
print("simulated conditions (gap m, GPS error m):", [(round(g), round(s, 1)) for g, s in CONDITIONS])

train, val = [], []                              # val: list of (trips, network, label)
for k, (gap, sig) in enumerate(CONDITIONS):
    G, edges = corridor(gap)
    train += prepare(make_trips(rng, 50, f"tr{k}", gap=gap, sigma=sig), edges)
    val.append((prepare(make_trips(rng, 12, f"va{k}", gap=gap, sigma=sig), edges), Network(G, edges)))
print("simulated points: train", sum(len(t["xy"]) for t in train), " validation", sum(len(t["xy"]) for va, _ in val for t in va))

acc, _, _ = evaluate_cv(train, FEATURES)
print(f"classifier on simulated trips it has not seen (5-fold, whole trips held out): accuracy {acc:.3f}")
model = fit(train, FEATURES)


def run(w, method):
    ys, ps = [], []
    for va, net in val:
        for t in va:
            p = p_service(model, t["feats"], FEATURES)
            if method == "nearest":
                g = group_pred(nearest(t["cands"]), net.grp)
            elif method == "hmm":
                g = group_pred(viterbi(t["xy"], t["cands"], net), net.grp)
            elif method == "ml":
                g = (p > 0.5).astype(int)
            else:
                g = group_pred(viterbi(t["xy"], t["cands"], net, bias=make_bias(p, t["cands"], net.grp, w)), net.grp)
            ys.append(t["label"])
            ps.append(g)
    return metrics(np.concatenate(ys), np.concatenate(ps))


best_w, best_acc = 0.5, -1.0
for w in [0.25, 0.5, 1, 2, 4]:
    a = run(w, "hybrid")["acc"]
    print(f"fusion weight {w}: validation accuracy {a:.3f}")
    if a > best_acc + 1e-9:
        best_w, best_acc = w, a
print("chosen weight:", best_w)

tab = pd.DataFrame({"nearest": run(0, "nearest"), "hmm": run(0, "hmm"), "ml": run(0, "ml"), "hybrid": run(best_w, "hybrid")}).T
print("\nSimulated validation trips, four methods:")
print(tab[["acc", "f1_macro", "n"]].round(3).to_string())
tab.to_csv(C.RES / "sim_results.csv")

imp = pd.Series(model.feature_importances_, index=FEATURES).sort_values(ascending=False)
imp.to_csv(C.RES / "feature_importance.csv", header=["importance"])
print("\nwhat the classifier relies on:")
print(imp.round(3).to_string())
joblib.dump({"model": model, "w": best_w}, C.PROC / "model.joblib")
print("\nsaved data/processed/model.joblib")