import matplotlib.pyplot as plt

from . import config as C
from .load import load_raw

df = load_raw()
print(df.head().to_string())
print("\ntrips:", df["trip"].nunique(), "  points:", len(df))
print("\npoints per trip:\n" + df.groupby("trip").size().to_string())
dt = df.sort_values(["trip", "t"]).groupby("trip")["t"].diff().dropna()
print("\nseconds between points:\n", dt.describe().round(2).to_string())
print(f"\nlat {df.lat.min():.5f} to {df.lat.max():.5f}   lon {df.lon.min():.5f} to {df.lon.max():.5f}")

trips = df["trip"].drop_duplicates().tolist()[:8]
fig, axs = plt.subplots(1, len(trips) + 1, figsize=(4 * (len(trips) + 1), 4.5))
axs[0].set_title("All trips on one map")
for ax, tid in zip(axs[1:], trips):
    d = df[df["trip"] == tid].sort_values("t")
    axs[0].plot(d.lon, d.lat, lw=1.2, label=str(tid))
    ax.plot(d.lon, d.lat, ".-", ms=2, lw=0.6)
    ax.plot(d.lon.iloc[0], d.lat.iloc[0], "go", label="start")
    ax.plot(d.lon.iloc[-1], d.lat.iloc[-1], "rs", label="end")
    ax.set_title(f"{tid} ({len(d)} points)")
    ax.ticklabel_format(useOffset=False)
axs[0].legend(fontsize=7)
axs[1].legend(fontsize=7)
for ax in axs:
    ax.set_xlabel("longitude")
    ax.set_ylabel("latitude")
    ax.tick_params(labelsize=7)
fig.tight_layout()
fig.savefig(C.RES / "overview.png", dpi=150)
print("saved results/overview.png")