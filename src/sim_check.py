"""Plots simulated speeds next to real speeds so you can see whether the simulator looks like your data."""
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from . import config as C
from .labels import attach
from .preprocess import derive_kinematics
from .simulator import make_trips

real = attach(pd.read_parquet(C.PROC / "points.parquet"))
sim = derive_kinematics(make_trips(np.random.default_rng(1), 100, "sim"))
fig, axs = plt.subplots(1, 2, figsize=(10, 3.8), sharey=True)
for ax, lab, name in zip(axs, (0, 1), ("main road", "service road")):
    ax.hist(real[real["label"] == lab]["speed_calc"].clip(0, 40), bins=40, range=(0, 40), density=True, alpha=0.6, label="real")
    ax.hist(sim[sim["label"] == lab]["speed_calc"].clip(0, 40), bins=40, range=(0, 40), density=True, alpha=0.6, label="simulated")
    ax.set_title(name)
    ax.set_xlabel("speed (m/s)")
    ax.legend()
fig.tight_layout()
fig.savefig(C.RES / "sim_vs_real_speed.png", dpi=150)
print("saved results/sim_vs_real_speed.png")
for lab, name in ((0, "main road"), (1, "service road")):
    r, s = real[real["label"] == lab]["speed_calc"], sim[sim["label"] == lab]["speed_calc"]
    print(f"{name}: real mean {r.mean():.1f} m/s (std {r.std():.1f})   simulated mean {s.mean():.1f} m/s (std {s.std():.1f})")