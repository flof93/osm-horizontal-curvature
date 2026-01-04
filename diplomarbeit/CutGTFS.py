import os
import zipfile
import pandas as pd
from io import BytesIO

# --- GTFS standard column dtypes ---
GTFS_DTYPES = {
    "agency.txt": {
        "agency_id": "string",
        "agency_name": "string",
        "agency_url": "string",
        "agency_timezone": "string",
        "agency_lang": "string",
        "agency_phone": "string",
        "agency_fare_url": "string",
        "agency_email": "string",
    },
    "stops.txt": {
        "stop_id": "string",
        "stop_code": "string",
        "stop_name": "string",
        "stop_desc": "string",
        "stop_lat": "float64",
        "stop_lon": "float64",
        "zone_id": "string",
        "stop_url": "string",
        "location_type": "Int64",
        "parent_station": "string",
        "stop_timezone": "string",
        "wheelchair_boarding": "Int64",
        "level_id": "string",
        "platform_code": "string",
    },
    "routes.txt": {
        "route_id": "string",
        "agency_id": "string",
        "route_short_name": "string",
        "route_long_name": "string",
        "route_desc": "string",
        "route_type": "Int64",
        "route_url": "string",
        "route_color": "string",
        "route_text_color": "string",
        "route_sort_order": "Int64",
        "continuous_pickup": "Int64",
        "continuous_drop_off": "Int64",
        "network_id": "string",
    },
    "trips.txt": {
        "route_id": "string",
        "service_id": "string",
        "trip_id": "string",
        "trip_headsign": "string",
        "trip_short_name": "string",
        "direction_id": "Int64",
        "block_id": "string",
        "shape_id": "string",
        "wheelchair_accessible": "Int64",
        "bikes_allowed": "Int64",
    },
    "stop_times.txt": {
        "trip_id": "string",
        "arrival_time": "string",
        "departure_time": "string",
        "stop_id": "string",
        "stop_sequence": "Int64",
        "stop_headsign": "string",
        "pickup_type": "Int64",
        "drop_off_type": "Int64",
        "continuous_pickup": "Int64",
        "continuous_drop_off": "Int64",
        "shape_dist_traveled": "float64",
        "timepoint": "Int64",
    },
    "calendar.txt": {
        "service_id": "string",
        "monday": "Int64",
        "tuesday": "Int64",
        "wednesday": "Int64",
        "thursday": "Int64",
        "friday": "Int64",
        "saturday": "Int64",
        "sunday": "Int64",
        "start_date": "string",
        "end_date": "string",
    },
    "calendar_dates.txt": {
        "service_id": "string",
        "date": "string",
        "exception_type": "Int64",
    },
    "shapes.txt": {
        "shape_id": "string",
        "shape_pt_lat": "float64",
        "shape_pt_lon": "float64",
        "shape_pt_sequence": "Int64",
        "shape_dist_traveled": "float64",
    },
    "fare_attributes.txt": {
        "fare_id": "string",
        "price": "float64",
        "currency_type": "string",
        "payment_method": "Int64",
        "transfers": "Int64",
        "agency_id": "string",
        "transfer_duration": "float64",
    },
    "fare_rules.txt": {
        "fare_id": "string",
        "route_id": "string",
        "origin_id": "string",
        "destination_id": "string",
        "contains_id": "string",
    },
    "feed_info.txt": {
        "feed_publisher_name": "string",
        "feed_publisher_url": "string",
        "feed_lang": "string",
        "default_lang": "string",
        "feed_start_date": "string",
        "feed_end_date": "string",
        "feed_version": "string",
        "feed_contact_email": "string",
        "feed_contact_url": "string",
    },
}

def read_gtfs_file(path_or_zipfile, name):
    """Read a GTFS text file safely with dtype support."""
    dtype = GTFS_DTYPES.get(name, None)
    try:
        return pd.read_csv(path_or_zipfile, dtype=dtype)
    except Exception as e:
        print(f"⚠️ Error reading {name}: {e}")
        return pd.DataFrame()

def split_gtfs_by_agency(gtfs_path, output_dir):
    """
    Splits a GTFS feed into multiple smaller feeds based on unique agency_id values in agency.txt.
    """
    os.makedirs(output_dir, exist_ok=True)

    # --- Step 1: Load GTFS feed ---
    files = {}
    if gtfs_path.endswith(".zip"):
        with zipfile.ZipFile(gtfs_path, "r") as zf:
            for name in zf.namelist():
                if name.endswith(".txt"):
                    with zf.open(name) as f:
                        files[name] = read_gtfs_file(f, name)
    else:
        for fname in os.listdir(gtfs_path):
            if fname.endswith(".txt"):
                files[fname] = read_gtfs_file(os.path.join(gtfs_path, fname), fname)

    if "agency.txt" not in files:
        raise ValueError("agency.txt not found in GTFS feed.")

    agency_df = files["agency.txt"]
    if "agency_id" not in agency_df.columns:
        agency_df["agency_id"] = "default"

    agencies = agency_df["agency_id"].unique()
    print(f"Found {len(agencies)} agencies: {list(agencies)}")

    # --- Step 2: Split feed ---
    for agency_id in agencies:
        print(f"Processing agency: {agency_id}")
        new_files = {}
        new_files["agency.txt"] = agency_df[agency_df["agency_id"] == agency_id]

        # routes
        if "routes.txt" in files:
            routes_df = files["routes.txt"]
            if "agency_id" in routes_df.columns:
                routes_filtered = routes_df[routes_df["agency_id"] == agency_id]
            else:
                routes_filtered = routes_df.copy()
            new_files["routes.txt"] = routes_filtered
        else:
            routes_filtered = pd.DataFrame()

        # trips
        if "trips.txt" in files and not routes_filtered.empty:
            trips_df = files["trips.txt"]
            trips_filtered = trips_df[trips_df["route_id"].isin(routes_filtered["route_id"])]
            new_files["trips.txt"] = trips_filtered
        else:
            trips_filtered = pd.DataFrame()

        # stop_times
        if "stop_times.txt" in files and not trips_filtered.empty:
            st_df = files["stop_times.txt"]
            st_filtered = st_df[st_df["trip_id"].isin(trips_filtered["trip_id"])]
            new_files["stop_times.txt"] = st_filtered

        # calendar
        if "calendar.txt" in files and not trips_filtered.empty:
            cal_df = files["calendar.txt"]
            new_files["calendar.txt"] = cal_df[cal_df["service_id"].isin(trips_filtered["service_id"])]

        # shapes
        if "shapes.txt" in files and "shape_id" in trips_filtered.columns:
            shape_df = files["shapes.txt"]
            new_files["shapes.txt"] = shape_df[shape_df["shape_id"].isin(trips_filtered["shape_id"])]

        # stops
        if "stops.txt" in files and "stop_times.txt" in new_files:
            stops_df = files["stops.txt"]
            stops_filtered = stops_df[stops_df["stop_id"].isin(new_files["stop_times.txt"]["stop_id"])]
            new_files["stops.txt"] = stops_filtered

        # optional feed_info.txt
        if "feed_info.txt" in files:
            new_files["feed_info.txt"] = files["feed_info.txt"]

        # --- Step 3: Write result ---
        agency_name = str(agency_id).replace(" ", "_").replace("/", "_")
        out_path = os.path.join(output_dir, f"gtfs_{agency_name}.zip")

        with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as outzip:
            for name, df in new_files.items():
                if not df.empty:
                    with BytesIO() as buffer:
                        df.to_csv(buffer, index=False)
                        outzip.writestr(name, buffer.getvalue())

        print(f"✅ Created {out_path}")

    print("All done!")

# --- Example usage ---
if __name__ == "__main__":
    gtfs_input = "../GTFS_Split/rbfreiburg.zip"  # path to your GTFS feed
    output_directory = "../GTFS_Split/freiburg/"
    split_gtfs_by_agency(gtfs_input, output_directory)
