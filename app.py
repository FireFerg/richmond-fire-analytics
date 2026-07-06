import json
from collections import Counter
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st
import plotly.express as px


st.set_page_config(
    page_title="Richmond Fire Analytics",
    page_icon="🔥",
    layout="wide",
)


def is_display_unit(unit):
    unit = str(unit).strip().upper()

    return (
        unit.startswith("E")
        or unit.startswith("TOWER")
        or unit.startswith("T")
        or unit.startswith("BC")
    )


def split_units(units):
    if not units:
        return []

    all_units = [u.strip().upper() for u in str(units).split(",") if u.strip()]

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


def apply_filters(
    df,
    units_df,
    selected_districts,
    selected_shifts,
    selected_stations,
    selected_types,
    selected_units,
    selected_date_range
):
    filtered = df.copy()

    if selected_districts:
        filtered = filtered[filtered["District"].isin(selected_districts)]

    if selected_shifts:
        filtered = filtered[filtered["Shift"].isin(selected_shifts)]

    if selected_stations:
        filtered = filtered[filtered["Station"].isin(selected_stations)]

    if selected_types:
        mask = filtered["Incident Type"].fillna("").apply(
            lambda x: any(t in x for t in selected_types)
        )
        filtered = filtered[mask]

    if selected_units:
        matching_incidents = units_df[
            units_df["Unit"].isin(selected_units)
        ]["Incident Number"].unique()

        filtered = filtered[
            filtered["Incident Number"].isin(matching_incidents)
        ]

    # Filter by date range
    if selected_date_range and len(selected_date_range) == 2:
        start_date, end_date = selected_date_range

        filtered = filtered[
            (filtered["Date"].dt.date >= start_date) &
            (filtered["Date"].dt.date <= end_date)
        ]

    return filtered

def value_counts_df(df, column, name):
    if df.empty or column not in df.columns:
        return pd.DataFrame(columns=[name, "Count"])
    out = (
        df[column]
        .replace("", pd.NA)
        .dropna()
        .value_counts()
        .reset_index()
    )
    out.columns = [name, "Count"]
    return out


def download_csv_button(df, label, filename):
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(label, csv, filename, "text/csv")


st.title("🔥 Richmond Fire Analytics Dashboard")

uploaded_file = st.sidebar.file_uploader("Upload a new incident export", type=["txt", "json"])
incidents_df, units_df = load_incidents(uploaded_file)

st.sidebar.header("Filters")

district_options = sorted([x for x in incidents_df["District"].dropna().unique() if x])
shift_options = sorted([x for x in incidents_df["Shift"].dropna().unique() if x])
station_options = sorted([x for x in incidents_df["Station"].dropna().unique() if x])
unit_options = sorted([x for x in units_df["Unit"].dropna().unique() if x])

type_counter = Counter()
for val in incidents_df["Incident Type"].dropna():
    for part in str(val).split(","):
        part = part.strip()
        if part:
            type_counter[part] += 1
type_options = sorted(type_counter.keys())

selected_districts = st.sidebar.multiselect("District", district_options)
selected_shifts = st.sidebar.multiselect("Shift", shift_options)
selected_stations = st.sidebar.multiselect("Station", station_options)
selected_units = st.sidebar.multiselect("Unit/Apparatus", unit_options)
selected_types = st.sidebar.multiselect("Incident Type", type_options)

# Date Range Filter
valid_dates = incidents_df["Date"].dropna()

if not valid_dates.empty:
    min_date = valid_dates.min().date()
    max_date = valid_dates.max().date()

    selected_date_range = st.sidebar.date_input(
        "Date Range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )
else:
    selected_date_range = None

filtered_df = apply_filters(
    incidents_df,
    units_df,
    selected_districts,
    selected_shifts,
    selected_stations,
    selected_types,
    selected_units,
    selected_date_range
)

filtered_units_df = units_df[units_df["Incident Number"].isin(filtered_df["Incident Number"])]

top_unit = filtered_units_df["Unit"].value_counts().index[0] if not filtered_units_df.empty else "N/A"
top_district = filtered_df["District"].replace("", pd.NA).dropna().value_counts().index[0] if not filtered_df.empty else "N/A"
top_shift = filtered_df["Shift"].replace("", pd.NA).dropna().value_counts().index[0] if not filtered_df.empty and filtered_df["Shift"].replace("", pd.NA).dropna().size else "N/A"

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Total Incidents", len(filtered_df))
col2.metric("Unique Units", filtered_units_df["Unit"].nunique() if not filtered_units_df.empty else 0)
col3.metric("Top Unit", top_unit)
col4.metric("Top District", top_district)
col5.metric("Top Shift", top_shift)

st.divider()

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Overview",
    "Incidents",
    "Unit Analysis",
    "District / Shift",
    "Map Export",
])

with tab1:
    left, right = st.columns(2)

    with left:
        st.subheader("Incidents by Shift")
        shift_counts = value_counts_df(filtered_df, "Shift", "Shift")
        st.bar_chart(shift_counts.set_index("Shift") if not shift_counts.empty else shift_counts)

        st.subheader("Top Incident Types")
        type_counts = Counter()
        for val in filtered_df["Incident Type"].dropna():
            for part in str(val).split(","):
                part = part.strip()
                if part:
                    type_counts[part] += 1
        type_df = pd.DataFrame(type_counts.most_common(15), columns=["Incident Type", "Count"])
        st.bar_chart(type_df.set_index("Incident Type") if not type_df.empty else type_df)

    with right:
        st.subheader("Top Districts")
        district_counts = value_counts_df(filtered_df, "District", "District").head(15)
        st.bar_chart(district_counts.set_index("District") if not district_counts.empty else district_counts)

        st.subheader("Top Stations")
        station_counts = value_counts_df(filtered_df, "Station", "Station").head(15)
        st.bar_chart(station_counts.set_index("Station") if not station_counts.empty else station_counts)

    st.subheader("Incidents Over Time")

if not filtered_df.empty and filtered_df["Date"].notna().any():

    time_scale = st.radio(
        "Time Scale",
        ["Daily", "Weekly", "Monthly"],
        horizontal=True
    )

    date_data = filtered_df.dropna(subset=["Date"]).copy()
    date_data["Date"] = pd.to_datetime(date_data["Date"])

    year = int(date_data["Date"].dt.year.mode()[0])

    full_daily_dates = pd.date_range(
        start=f"{year}-01-01",
        end=f"{year}-12-31",
        freq="D"
    )

    daily_counts = (
        date_data
        .groupby("Date")
        .size()
        .rename("Incidents")
        .reindex(full_daily_dates, fill_value=0)
        .rename_axis("Date")
        .reset_index()
    )

    if time_scale == "Daily":
        chart_data = daily_counts.copy()
        chart_data["7-Day Average"] = chart_data["Incidents"].rolling(
            window=7,
            min_periods=1
        ).mean()

        fig = px.line(
            chart_data,
            x="Date",
            y=["Incidents", "7-Day Average"],
            title="Daily Incidents With 7-Day Average",
            labels={
                "value": "Incident Count",
                "variable": "Metric"
            }
        )

    elif time_scale == "Weekly":
        chart_data = (
            daily_counts
            .set_index("Date")
            .resample("W")
            .sum()
            .reset_index()
        )

        fig = px.line(
            chart_data,
            x="Date",
            y="Incidents",
            title="Weekly Incident Totals",
            labels={
                "Incidents": "Incident Count"
            }
        )

    else:
        chart_data = (
            daily_counts
            .set_index("Date")
            .resample("ME")
            .sum()
            .reset_index()
        )

        fig = px.line(
            chart_data,
            x="Date",
            y="Incidents",
            title="Monthly Incident Totals",
            labels={
                "Incidents": "Incident Count"
            }
        )

    fig.update_layout(
        hovermode="x unified",
        height=450,
        margin=dict(l=20, r=20, t=60, b=20)
    )

    st.plotly_chart(fig, use_container_width=True)

else:
    st.info("No date data available.")
with tab2:
    st.subheader("Master Incident Table")
    display_cols = [
        "Incident Number", "Date/Time", "Address", "District", "Station",
        "Shift", "Incident Type", "Units", "Unit Count"
    ]
    st.dataframe(filtered_df[display_cols], use_container_width=True, height=500)
    download_csv_button(filtered_df, "Download Filtered Incidents CSV", "filtered_incidents.csv")

with tab3:
    st.subheader("Unit Frequency")
    unit_counts = (
        filtered_units_df["Unit"].value_counts().reset_index()
        if not filtered_units_df.empty else pd.DataFrame(columns=["Unit", "Count"])
    )
    if not unit_counts.empty:
        unit_counts.columns = ["Unit", "Count"]
    st.dataframe(unit_counts, use_container_width=True)
    st.bar_chart(unit_counts.head(20).set_index("Unit") if not unit_counts.empty else unit_counts)

    st.subheader("Unit by Shift")
    if not filtered_units_df.empty:
        unit_shift = pd.crosstab(filtered_units_df["Unit"], filtered_units_df["Shift"])
        unit_shift["Total"] = unit_shift.sum(axis=1)
        unit_shift = unit_shift.sort_values("Total", ascending=False)
        st.dataframe(unit_shift, use_container_width=True)
    else:
        st.info("No unit data available.")

with tab4:
    st.subheader("District by Shift")
    if not filtered_df.empty:
        district_shift = pd.crosstab(filtered_df["District"], filtered_df["Shift"])
        district_shift["Total"] = district_shift.sum(axis=1)
        district_shift = district_shift.sort_values("Total", ascending=False)
        st.dataframe(district_shift, use_container_width=True)

        st.subheader("Hour of Day")
        hour_counts = filtered_df.dropna(subset=["Hour"]).groupby("Hour").size().reset_index(name="Count")
        st.bar_chart(hour_counts.set_index("Hour") if not hour_counts.empty else hour_counts)
    else:
        st.info("No incident data available.")

with tab5:
    st.subheader("Google My Maps Export")
    map_cols = ["Incident Number", "Address", "Full Address", "Date/Time", "District", "Station", "Shift", "Incident Type", "Units"]
    map_df = filtered_df[map_cols].copy()
    map_df = map_df[map_df["Address"].fillna("") != ""]
    map_df = map_df.rename(columns={"Incident Number": "Name"})
    st.dataframe(map_df, use_container_width=True, height=400)
    download_csv_button(map_df, "Download Google My Maps CSV", "google_my_maps_import_filtered.csv")

    st.markdown(
        """
        **Google My Maps steps:**
        1. Go to `mymaps.google.com`
        2. Create a new map
        3. Import this CSV
        4. Choose **Full Address** as the location column
        5. Choose **Name** as the marker title
        6. Style by **District**, **Shift**, or **Incident Type**
        """
    )
