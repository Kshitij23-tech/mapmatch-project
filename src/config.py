from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
TRIPS = ROOT / "data" / "trips"      # one CSV per trip, written by src/convert_pos.py
PROC = ROOT / "data" / "processed"
RES = ROOT / "results"
for _p in (PROC, RES, TRIPS):
    _p.mkdir(parents=True, exist_ok=True)

# ---------- Described the trip files----------
TABLE_EXT = {".csv"}             # file types read from data/trips
SEP = ","                        # column separator
COLS = {
    "trip": None,                # column that identifies a trip; None = one file is one trip
    "time": "timestamp",         # time column (text timestamps or numbers)
    "lat": "latitude",
    "lon": "longitude",
    "speed": None,               # reported speed column, or None (only used as a sanity check)
    "height": "height",          # height column (metres); kept for later, or None
}
TIME_NUMERIC_SCALE = 1.0         # seconds per unit if time is a number (0.001 if milliseconds)
SPLIT_GAP_S = None               # e.g. 300 splits a file into trips wherever time jumps by 5 minutes
MAX_ROWS = 500_000               # rows read per file while developing; None = everything
STUDY_BBOX = None                # None = use all points. Or (lat_min, lat_max, lon_min, lon_max) to keep one area

# ---------- Matching and features ----------
MAX_SPEED_MS = 60.0              # faster than this between two points = GPS jump
MIN_POINTS = 15                  # trips shorter than this are dropped
SEARCH_RADIUS_M = 60.0           # candidate roads within this distance of a point
MAX_CANDS = 10                   # keep at most this many candidates per point
SIGMA_M = 10.0                   # assumed GPS error (metres) in the emission probability
BETA_M = 5.0                     # transition scale: how much route/straight-line mismatch is tolerated
ROUTE_CUTOFF_M = 1500.0          # ignore routes longer than this
BACK_TOL_M = 15.0                # allowed backwards drift on the same road (GPS noise)
NO_ROUTE_PENALTY = 30.0          # log-penalty when two candidates are not connected
WINDOW = 5                       # points in the motion-feature window
GEO_WINDOW = 9                   # points in the geometry-feature window