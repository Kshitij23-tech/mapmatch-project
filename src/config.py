from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
TRIPS = ROOT / "data" / "trips"      # one CSV per dataset, written by src/convert_pos.py
PROC = ROOT / "data" / "processed"
RES = ROOT / "results"
LABELS = ROOT / "data" / "labels.csv"
for _p in (PROC, RES, TRIPS):
    _p.mkdir(parents=True, exist_ok=True)

# ---------- Describe the trip files (these defaults fit the converted ISRO files) ----------
TABLE_EXT = {".csv"}
SEP = ","
COLS = {
    "trip": None,                # None = one file is one trip
    "time": "timestamp",
    "lat": "latitude",
    "lon": "longitude",
    "speed": None,
    "height": "height",
}
TIME_NUMERIC_SCALE = 1.0
SPLIT_GAP_S = None
MAX_ROWS = 500_000

# ---------- Which OpenStreetMap roads count as main road and service road ----------
# Day 1 prints a table; change these sets if the table shows your roads carry other tags.
MAIN_TAGS = {"motorway", "motorway_link"}
SERVICE_TAGS = {"primary", "primary_link", "secondary", "tertiary", "service"}
MAIN_WORDS = ["Expressway"]
SERVICE_WORDS = ["Mysuru Road", "Mysore Road", "Highway", "Service"]
# Datasets that are known to be entirely one road type (0 = main road, 1 = service road)
TRIP_KNOWN = {"Dataset1": 0, "Dataset2": 1}

# Places where the road names mean something different from the rest of the area.
# Near Dataset5 the flyover is named "Highway" and the roads on the ground are "Expressway" / "Service lane".
AREA_RULES = [{"trip": "Dataset5", "main_words": ["Highway"], "service_words": ["Expressway", "Service"]}]

# ---------- Matching (tuned on Day 4) ----------
MAX_SPEED_MS = 60.0
MIN_POINTS = 15
SEARCH_RADIUS_M = 60.0
MAX_CANDS = 10
SIGMA_M = 5.0
BETA_M = 5.0
ROUTE_CUTOFF_M = 1500.0
BACK_TOL_M = 15.0
NO_ROUTE_PENALTY = 30.0
WINDOW = 5
GEO_WINDOW = 9

# ---------- Simulator (set from the numbers printed on Day 5) ----------
SIM_GAP_M = 20.0                 # distance between main road and service road
SIM_SIGMA_M = 6.0                # GPS error of the simulated receiver
V_HW = 22.0                      # typical speed on the main road (m/s)
V_SR = 17.0                      # typical speed on the service road (m/s)
SIM_STOP_P = 0.003               # chance per second that a service-road vehicle stops