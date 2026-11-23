import numpy as np
import pandas as pd

from . import config as C

MOTION = ["sp_mean", "sp_std", "sp_min", "sp_max", "acc_absmax", "stop_frac", "hd_rate"]
GEOM = ["dH", "dS", "dHS", "dHS_mean"]
FEATURES = MOTION + GEOM


def trip_features(d, cands, grp):
    """One row of features per GPS point. d is one trip after derive_kinematics, index 0..n-1."""
    def roll(s, w=None):
        return s.rolling(w or C.WINDOW, center=True, min_periods=1)

    f = pd.DataFrame(index=d.index)
    sp = d["speed_calc"]
    f["sp_mean"] = roll(sp).mean()
    f["sp_std"] = roll(sp).std().fillna(0.0)
    f["sp_min"] = roll(sp).min()
    f["sp_max"] = roll(sp).max()
    f["acc_absmax"] = roll(d["accel"].abs()).max()
    f["stop_frac"] = roll((sp < 1.0).astype(float)).mean()
    hd = d["heading_calc"].to_numpy()
    turn = np.abs((np.diff(hd, prepend=hd[0]) + 180) % 360 - 180)
    f["hd_rate"] = roll(pd.Series(turn, index=d.index)).mean()

    dH = np.full(len(d), C.SEARCH_RADIUS_M)
    dS = dH.copy()
    for i, cl in enumerate(cands):
        for e, dist, _ in cl:
            if grp[e] == 0:
                dH[i] = min(dH[i], dist)
            elif grp[e] == 1:
                dS[i] = min(dS[i], dist)
    f["dH"], f["dS"] = dH, dS
    f["dHS"] = f["dH"] - f["dS"]                       # negative: closer to the highway
    f["dHS_mean"] = roll(f["dHS"], C.GEO_WINDOW).mean()
    return f