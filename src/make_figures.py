import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from . import config as C

NAMES = {"nearest": "Nearest road", "hmm": "HMM", "ml": "Classifier", "hybrid": "HMM + classifier", "leuven": "LeuvenMapMatching",
         "ml_real": "Classifier (real-trained)", "hybrid_real": "HMM + classifier (real-trained)"}
COL = {"nearest": "#9ca3af", "hmm": "#0d8f8f", "ml": "#7c8aa5", "hybrid": "#e08a00", "leuven": "#6d28d9",
       "ml_real": "#b0b8c8", "hybrid_real": "#f2c46d"}
bt = pd.read_csv(C.RES / "real_by_trip.csv")
methods = [m for m in NAMES if m in set(bt["method"])]
trips = sorted(bt["trip"].unique())


def bars(value, ylabel, fname, title):
    fig, ax = plt.subplots(figsize=(10, 4))
    w = 0.8 / len(methods)
    for k, m in enumerate(methods):
        v = bt[bt["method"] == m].set_index("trip").loc[trips, value]
        ax.bar(np.arange(len(trips)) + k * w, v, w, label=NAMES[m], color=COL[m])
    ax.set_xticks(np.arange(len(trips)) + 0.4 - w / 2)
    ax.set_xticklabels(trips)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.legend(fontsize=8, ncol=2)
    fig.tight_layout()
    fig.savefig(C.RES / fname, dpi=150)
    plt.close(fig)


bars("acc", "accuracy", "fig_accuracy.png", "Share of points given the right road, per dataset")
bars("dist_err_m", "error (metres)", "fig_distance_error.png", "Error of the distance travelled on the main road")
try:
    imp = pd.read_csv(C.RES / "feature_importance.csv", index_col=0)["importance"].sort_values()
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.barh(imp.index, imp.values, color="#0d8f8f")
    ax.set_xlabel("importance")
    ax.set_title("What the classifier relies on")
    fig.tight_layout()
    fig.savefig(C.RES / "fig_features.png", dpi=150)
except FileNotFoundError:
    pass
print("saved results/fig_accuracy.png, fig_distance_error.png, fig_features.png")