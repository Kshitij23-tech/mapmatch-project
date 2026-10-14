"""Turns the ISRO *.pos files (GNSS receiver solutions) into one clean CSV per trip in data/trips."""
import re
from pathlib import Path

import pandas as pd

from . import config as C

DATE = re.compile(r"^\d{4}[/-]\d{2}[/-]\d{2}$")


def read_pos(path):
    rows = []
    for line in Path(path).read_text(errors="ignore").splitlines():
        s = line.strip()
        if not s or s.startswith("%"):               # header and comment lines start with %
            continue
        p = s.split()
        if len(p) < 5 or not DATE.match(p[0]):
            continue
        rows.append({"timestamp": p[0] + " " + p[1], "latitude": float(p[2]), "longitude": float(p[3]),
                     "height": float(p[4]), "q": int(p[5]) if len(p) > 5 and p[5].isdigit() else None})
    if not rows:
        head = "\n".join(Path(path).read_text(errors="ignore").splitlines()[:15])
        raise SystemExit(f"No data rows found in {path}. The first lines are:\n{head}\n"
                         "Copy these lines into a chat so the reader can be adjusted to this format.")
    df = pd.DataFrame(rows)
    if not (df["latitude"].between(-90, 90).all() and df["longitude"].between(-180, 180).all()):
        raise SystemExit(f"{path}: latitude/longitude are not plain decimal degrees. Show the first lines of the file.")
    return df


def main():
    files = sorted(C.RAW.rglob("*.pos"))
    if not files:
        raise SystemExit("No .pos files found under data/raw")
    C.TRIPS.mkdir(parents=True, exist_ok=True)
    for f in files:
        df = read_pos(f)
        out = C.TRIPS / f"{f.stem}.csv"
        df.to_csv(out, index=False)
        t = pd.to_datetime(df["timestamp"])
        step = t.diff().dt.total_seconds().median()
        print(f"{f.stem}: {len(df)} points, {(t.iloc[-1] - t.iloc[0]).total_seconds():.0f} s, "
              f"typical step {step:.2f} s, lat {df.latitude.min():.5f}..{df.latitude.max():.5f}, "
              f"lon {df.longitude.min():.5f}..{df.longitude.max():.5f}, solution quality Q: "
              f"{df['q'].value_counts().to_dict()}")
    print("written to", C.TRIPS)


if __name__ == "__main__":
    main()