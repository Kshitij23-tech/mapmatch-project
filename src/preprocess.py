import json

import numpy as np
import pandas as pd
from pyproj import Transformer

from . import config as C
from .load import load_raw


def utm_epsg(lat, lon):
    zone = int((lon + 180) // 6) + 1
    return (32600 if lat >= 0 else 32700) + zone


def clean(df):
    df = df.dropna(subset=["trip", "t", "lat", "lon"])
    df = df[df["lat"].between(-90, 90) & df["lon"].between(-180, 180)]
    df = df.sort_values(["trip", "t"]).drop_duplicates(["trip", "t"])
    return df.reset_index(drop=True)


def project(df):
    epsg = utm_epsg(df["lat"].mean(), df["lon"].mean())
    tr = Transformer.from_crs(4326, epsg, always_xy=True)
    x, y = tr.transform(df["lon"].to_numpy(), df["lat"].to_numpy())
    df = df.copy()
    df["x"], df["y"] = x, y
    return df, epsg


def drop_jumps(df, vmax=None):
    vmax = vmax or C.MAX_SPEED_MS
    for _ in range(3):
        g = df.groupby("trip", sort=False)
        step = np.hypot(g["x"].diff(), g["y"].diff())
        bad = (step / g["t"].diff()) > vmax
        if not bad.any():
            break
        df = df[~bad].reset_index(drop=True)
    return df


def drop_short(df):
    n = df.groupby("trip")["t"].transform("size")
    return df[n >= C.MIN_POINTS].reset_index(drop=True)


def derive_kinematics(df):
    """Adds dt, speed_calc (m/s), heading_calc (degrees) and accel (m/s^2) for every trip."""
    df = df.copy()
    g = df.groupby("trip", sort=False)
    dx, dy = g["x"].diff(), g["y"].diff()
    df["dt"] = g["t"].diff()
    df["speed_calc"] = np.hypot(dx, dy) / df["dt"]
    df["heading_calc"] = (np.degrees(np.arctan2(dx, dy)) + 360) % 360
    g = df.groupby("trip", sort=False)
    df["accel"] = g["speed_calc"].diff() / df["dt"]
    cols = ["dt", "speed_calc", "heading_calc", "accel"]
    df[cols] = df.groupby("trip", sort=False)[cols].bfill()
    df[cols] = df[cols].fillna(0.0)
    return df


def run():
    raw = load_raw()
    before = raw.groupby("trip").size()
    df = clean(raw)
    df, epsg = project(df)
    df = drop_jumps(df)
    df = drop_short(df)
    df = derive_kinematics(df)
    df.to_parquet(C.PROC / "points.parquet", index=False)
    (C.PROC / "meta.json").write_text(json.dumps({"epsg": int(epsg), "trips": int(df["trip"].nunique()), "points": int(len(df))}))
    after = df.groupby("trip").size()
    print(f"metric CRS: EPSG:{epsg}")
    print(pd.DataFrame({"points_in_file": before, "points_kept": after}).to_string())
    s = df.groupby("trip")["speed_calc"].agg(["mean", "std", "max"]).round(1)
    s["mean_kmh"] = (s["mean"] * 3.6).round(0)
    print("\nspeed per dataset (m/s):")
    print(s.to_string())
    print("\nsaved data/processed/points.parquet")
    return df


if __name__ == "__main__":
    run()