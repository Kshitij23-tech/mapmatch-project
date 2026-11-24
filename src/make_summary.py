"""Collects the final numbers into results/summary.md so they can be pasted into the report."""
import pandas as pd

from . import config as C

NAMES = {"nearest": "Nearest road", "hmm": "HMM matcher", "ml": "Classifier (trained on simulation)", "hybrid": "HMM + classifier", "leuven": "LeuvenMapMatching (existing library)",
         "ml_real": "Classifier (trained on the other real datasets)", "hybrid_real": "HMM + classifier (real-trained)"}


def md(df):
    cols = list(df.columns)
    lines = ["| " + " | ".join(map(str, cols)) + " |", "|" + "---|" * len(cols)]
    for _, r in df.iterrows():
        lines.append("| " + " | ".join(str(int(v)) if c in ("n", "points") else (f"{v:.3f}" if isinstance(v, float) else str(v))
                                         for c, v in zip(cols, r)) + " |")
    return "\n".join(lines)


pooled = pd.read_csv(C.RES / "real_pooled.csv")
bt = pd.read_csv(C.RES / "real_by_trip.csv")
order = [m for m in NAMES if m in set(pooled["method"])]
txt = ["# Results summary", "", "## All five datasets together (every scored point)", ""]
p = pooled.set_index("method").loc[order].reset_index()
p["method"] = p["method"].map(NAMES)
txt += [md(p[["method", "acc", "f1_macro", "prec_main", "rec_main", "prec_serv", "rec_serv", "n"]]), ""]
txt += ["## Accuracy per dataset", ""]
a = bt.pivot(index="trip", columns="method", values="acc")[order].rename(columns=NAMES).reset_index()
txt += [md(a), ""]
txt += ["## Distance on the main road per dataset (metres)", ""]
ref = bt.drop_duplicates("trip").set_index("trip")["ref_main_m"].round(0).rename("Reference")
dist = bt.pivot(index="trip", columns="method", values="pred_main_m")[order].round(0).rename(columns=NAMES)
txt += [md(pd.concat([ref, dist], axis=1).reset_index()), ""]
txt += ["## Error of the main-road distance (metres)", ""]
e = bt.pivot(index="trip", columns="method", values="dist_err_m")[order].round(0).rename(columns=NAMES).reset_index()
txt += [md(e), ""]
txt += ["## Road changes found within 5 s (found / true / extra predicted)", ""]
bt["s"] = bt["switch_found"].astype(str) + " / " + bt["switch_true"].astype(str) + " / " + bt["switch_extra"].astype(str)
s = bt.pivot(index="trip", columns="method", values="s")[order].rename(columns=NAMES).reset_index()
txt += [md(s), ""]
try:
    sim = pd.read_csv(C.RES / "sim_results.csv", index_col=0)[["acc", "f1_macro", "n"]].reset_index().rename(columns={"index": "method"})
    sim["method"] = sim["method"].map(NAMES)
    txt += ["## Simulated validation trips (training ground)", "", md(sim), ""]
    imp = pd.read_csv(C.RES / "feature_importance.csv", index_col=0).reset_index().rename(columns={"index": "feature"})
    txt += ["## Feature importance of the classifier", "", md(imp), ""]
except FileNotFoundError:
    pass
(C.RES / "summary.md").write_text("\n".join(txt))
print("\n".join(txt))
print("\nsaved results/summary.md")