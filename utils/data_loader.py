import json
from pathlib import Path

import pandas as pd
import streamlit as st

def is_display_unit(unit):
    unit = str(unit).strip().upper()

    return (
        unit.startswith("E")
        or unit.startswith("TOWER")
        or unit.startswith("T")
        or unit.startswith("BC")
    )


def normalize_unit(unit):
    unit = str(unit).strip().upper()

    if unit == "TOWER5":
        return "T5"

    return unit


def is_display_unit(unit):
    unit = normalize_unit(unit)

    return (
        unit.startswith("E")
        or unit.startswith("T")
        or unit.startswith("BC")
    )


def split_units(units):
    if not units:
        return []

    all_units = [normalize_unit(u) for u in str(units).split(",") if u.strip()]

    return [u for u in all_units if is_display_unit(u)]

def parse_datetime(value):
    if not value:
        return pd.NaT
    try:
        return pd.to_datetime(value)
    except Exception:
        return pd.NaT


@st.cache_data
def load_incidents(file):
    if file is not None:
        raw = file.read().decode("utf-8", errors="ignore")
    else:
        default_path = Path("data/Incidents.txt")
        if not default_path.exists():
            st.error("No file uploaded and data/Incidents.txt was not found.")
            st.stop()
        raw = default_path.read_text(errors="ignore")

    data = json.loads(raw)
    incidents = data.get("incidents", [])

    rows = []
    unit_rows = []

    for inc in incidents:
        dt = parse_datetime(inc.get("incidentOnsetDateTime"))
        units = inc.get("units", "") or ""
        unit_list = split_units(units)

        row = {
            "Incident ID": inc.get("incidentId", ""),
            "Incident Number": inc.get("incidentNumber", ""),
            "Date/Time": dt,
            "Date": dt.date() if not pd.isna(dt) else None,
            "Hour": int(dt.hour) if not pd.isna(dt) else None,
            "Address": inc.get("streetAddress", ""),
            "Full Address": f"{inc.get('streetAddress', '')}, Richmond, VA" if inc.get("streetAddress") else "",
            "District": str(inc.get("district", "") or "").strip(),
            "Station": str(inc.get("station", "") or "").strip(),
            "Shift": str(inc.get("shift", "") or "").strip(),
            "Zone": inc.get("zone", ""),
            "Incident Type": inc.get("types", ""),
            "Units": units,
            "Unit Count": len(unit_list),
            "Report Writer": inc.get("reportWriter", ""),
        }
        rows.append(row)

        for unit in unit_list:
            unit_rows.append({
                "Incident Number": row["Incident Number"],
                "Date/Time": row["Date/Time"],
                "Date": row["Date"],
                "Hour": row["Hour"],
                "Address": row["Address"],
                "District": row["District"],
                "Station": row["Station"],
                "Shift": row["Shift"],
                "Incident Type": row["Incident Type"],
                "Unit": unit,
            })

    incidents_df = pd.DataFrame(rows)
    units_df = pd.DataFrame(unit_rows)

    if not incidents_df.empty:
        incidents_df["Date/Time"] = pd.to_datetime(incidents_df["Date/Time"], errors="coerce")
        incidents_df["Date"] = pd.to_datetime(incidents_df["Date"], errors="coerce")
    if not units_df.empty:
        units_df["Date/Time"] = pd.to_datetime(units_df["Date/Time"], errors="coerce")
        units_df["Date"] = pd.to_datetime(units_df["Date"], errors="coerce")

    return incidents_df, units_df
