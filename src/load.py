import pandas as pd

from . import config as C


def to_seconds(s):
    if pd.api.types.is_numeric_dtype(s):
        return s.astype(float) * C.TIME_NUMERIC_SCALE
    dt = pd.to_datetime(s, errors="coerce")
    return (dt - dt.min()).dt.total_seconds()


def load_raw():
    files = sorted(p for p in C.TRIPS.rglob("*") if p.is_file() and p.suffix.lower() in C.TABLE_EXT)
    if not files:
        raise SystemExit("No trip files found in data/trips. Run: python -m src.convert_pos")
    parts = []
    for p in files:
        d = pd.read_csv(p, sep=C.SEP, nrows=C.MAX_ROWS)
        if C.COLS["trip"] is None:
            d["trip"] = p.stem
        parts.append(d)
    df = pd.concat(parts, ignore_index=True)
    df = df.rename(columns={v: k for k, v in C.COLS.items() if v})
    df["t"] = to_seconds(df["time"])
    df = df[[c for c in ["trip", "t", "lat", "lon", "speed", "height"] if c in df.columns]].copy()
    df["trip"] = df["trip"].astype(str)
    if C.SPLIT_GAP_S:
        df = df.sort_values(["trip", "t"])
        jump = (df.groupby("trip")["t"].diff() > C.SPLIT_GAP_S).astype(int)
        df["trip"] = df["trip"] + "_" + jump.groupby(df["trip"]).cumsum().astype(str)
    return df.reset_index(drop=True)