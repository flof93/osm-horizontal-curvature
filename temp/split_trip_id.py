import pandas as pd
from pathlib import Path
import shutil

# ==============================
# KONFIGURATION
# ==============================
INPUT_DIR = Path("delijn")
OUTPUT_DIR = Path("delijn_GTRA")
TRIP_FILTER = "GTRA"

# ==============================
# HILFSFUNKTIONEN
# ==============================
def load_txt(filename):
    path = INPUT_DIR / filename
    if not path.exists():
        return None
    return pd.read_csv(path)

def save_txt(df, filename):
    if df is None:
        return
    df.to_csv(OUTPUT_DIR / filename, index=False)

# ==============================
# VORBEREITUNG
# ==============================
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

print("GTFS-Bereinigung gestartet...")

# ==============================
# TRIPS FILTERN
# ==============================
trips = load_txt("trips.txt")
if trips is None:
    raise RuntimeError("trips.txt fehlt – Abbruch")

filtered_trips = trips[trips["trip_id"].str.contains(TRIP_FILTER, na=False)]

print(f"Trips vorher: {len(trips)}")
print(f"Trips nach Filter: {len(filtered_trips)}")

# ==============================
# ROUTES REDUZIEREN
# ==============================
routes = load_txt("routes.txt")
used_route_ids = filtered_trips["route_id"].unique()
filtered_routes = routes[routes["route_id"].isin(used_route_ids)]

# ==============================
# STOP_TIMES REDUZIEREN
# ==============================
stop_times = load_txt("stop_times.txt")
filtered_stop_times = stop_times[
    stop_times["trip_id"].isin(filtered_trips["trip_id"])
]

# ==============================
# STOPS REDUZIEREN
# ==============================
stops = load_txt("stops.txt")
used_stop_ids = filtered_stop_times["stop_id"].unique()
filtered_stops = stops[stops["stop_id"].isin(used_stop_ids)]

# ==============================
# SERVICES (calendar / calendar_dates)
# ==============================
used_service_ids = filtered_trips["service_id"].unique()

calendar = load_txt("calendar.txt")
filtered_calendar = None
if calendar is not None:
    filtered_calendar = calendar[
        calendar["service_id"].isin(used_service_ids)
    ]

calendar_dates = load_txt("calendar_dates.txt")
filtered_calendar_dates = None
if calendar_dates is not None:
    filtered_calendar_dates = calendar_dates[
        calendar_dates["service_id"].isin(used_service_ids)
    ]

# ==============================
# SHAPES REDUZIEREN
# ==============================
shapes = load_txt("shapes.txt")
filtered_shapes = None
if shapes is not None and "shape_id" in filtered_trips.columns:
    used_shape_ids = filtered_trips["shape_id"].dropna().unique()
    filtered_shapes = shapes[shapes["shape_id"].isin(used_shape_ids)]

# ==============================
# AGENCY (unverändert kopieren)
# ==============================
agency = load_txt("agency.txt")

# ==============================
# DATEIEN SPEICHERN
# ==============================
save_txt(agency, "agency.txt")
save_txt(filtered_routes, "routes.txt")
save_txt(filtered_trips, "trips.txt")
save_txt(filtered_stop_times, "stop_times.txt")
save_txt(filtered_stops, "stops.txt")
save_txt(filtered_calendar, "calendar.txt")
save_txt(filtered_calendar_dates, "calendar_dates.txt")
save_txt(filtered_shapes, "shapes.txt")

# ==============================
# OPTIONALE DATEIEN 1:1 KOPIEREN
# ==============================
OPTIONAL_FILES = [
    "fare_attributes.txt",
    "fare_rules.txt",
    "feed_info.txt",
    "transfers.txt",
    "levels.txt",
    "pathways.txt"
]

for fname in OPTIONAL_FILES:
    src = INPUT_DIR / fname
    if src.exists():
        shutil.copy(src, OUTPUT_DIR / fname)

print("✅ GTFS-Bereinigung abgeschlossen.")
print(f"📂 Neuer Feed: {OUTPUT_DIR.resolve()}")
