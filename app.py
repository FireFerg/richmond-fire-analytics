from collections import Counter

import pandas as pd
import streamlit as st
import plotly.express as px

from utils.data_loader import load_incidents

st.set_page_config(
    page_title="Richmond Fire Analytics",
    page_icon="🔥",
    layout="wide",
)


def load_css(file_path):
    with open(file_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


load_css("styles/main.css")


load_css("styles/main.css")

with st.sidebar:
    st.markdown(
        """
        <div class="sidebar-title">RICHMOND<br>FIRE ANALYTICS</div>
        <div class="sidebar-subtitle">Incident Intelligence</div>

        <div class="sidebar-nav-item sidebar-nav-item-active">📊 Overview</div>
        <div class="sidebar-nav-item">🗺️ Map</div>
        <div class="sidebar-nav-item">🚒 Companies</div>
        <div class="sidebar-nav-item">🏢 Districts</div>
        <div class="sidebar-nav-item">📄 Reports</div>
        <div class="sidebar-nav-item">ℹ️ About</div>
        """,
        unsafe_allow_html=True
    )



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


st.markdown(
    """
    <div style="
        background: linear-gradient(90deg, #7f0000, #d7263d);
        padding: 24px;
        border-radius: 14px;
        margin-bottom: 20px;
    ">
        <h1 style="color: white; margin: 0; font-size: 38px;">
            🔥 Richmond Fire Analytics
        </h1>
        <p style="color: #f5f5f5; margin: 6px 0 0 0; font-size: 17px;">
            Incident trends, unit activity, district workload, and operational insights
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

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

# Count all displayed units
unit_counts = (
    filtered_units_df["Unit"].value_counts()
    if not filtered_units_df.empty
    else pd.Series(dtype=int)
)

# Engines only
engine_counts = unit_counts[
    unit_counts.index.str.startswith("E")
] if not unit_counts.empty else pd.Series(dtype=int)

# Trucks (T and TOWER are already normalized to T)
truck_counts = unit_counts[
    unit_counts.index.str.startswith("T")
] if not unit_counts.empty else pd.Series(dtype=int)

top_engine = engine_counts.index[0] if not engine_counts.empty else "N/A"
top_truck = truck_counts.index[0] if not truck_counts.empty else "N/A"

top_engine_count = int(engine_counts.iloc[0]) if not engine_counts.empty else 0
top_truck_count = int(truck_counts.iloc[0]) if not truck_counts.empty else 0

top_district = (
    filtered_df["District"]
    .replace("", pd.NA)
    .dropna()
    .value_counts()
    .index[0]
    if not filtered_df.empty
    and filtered_df["District"].replace("", pd.NA).dropna().size
    else "N/A"
)

top_shift = (
    filtered_df["Shift"]
    .replace("", pd.NA)
    .dropna()
    .value_counts()
    .index[0]
    if not filtered_df.empty
    and filtered_df["Shift"].replace("", pd.NA).dropna().size
    else "N/A"
)

district_incident_count = (
    int(
        filtered_df["District"]
        .replace("", pd.NA)
        .dropna()
        .value_counts()
        .iloc[0]
    )
    if not filtered_df.empty
    and filtered_df["District"].replace("", pd.NA).dropna().size
    else 0
)

top_shift_count = (
    int(
        filtered_df["Shift"]
        .replace("", pd.NA)
        .dropna()
        .value_counts()
        .iloc[0]
    )
    if not filtered_df.empty
    and filtered_df["Shift"].replace("", pd.NA).dropna().size
    else 0
)

def kpi_card(title, value, icon, note="", color="#ef233c"):
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-icon" style="color:{color};">{icon}</div>
            <div class="kpi-label">{title}</div>
            <div class="kpi-value">{value}</div>
            <div class="kpi-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    kpi_card(
    "Total Incidents",
    len(filtered_df),
    "🔥",
    "Selected dataset",
    "#ef233c"
)
with col2:
    kpi_card(
    "Top Engine",
    top_engine,
    "🚒",
    f"{top_engine_count} responses",
    "#ef233c"
)

with col3:
    kpi_card(
    "Top Truck",
    top_truck,
    "🚛",
    f"{top_truck_count} responses",
    "#ef233c"
)

with col4:
    kpi_card(
    "Top District",
    top_district,
    "📍",
    f"{district_incident_count} incidents",
    "#ef233c"
)

with col5:
    kpi_card(
    "Top Shift",
    top_shift,
    "🕒",
    f"{top_shift_count} incidents",
    "#ef233c"
)

st.divider()

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Overview",
    "Incidents",
    "Unit Analysis",
    "District / Shift",
    "Map Export",
])

with tab1:
    st.markdown("""
<div class="section-spacing">
    <div class="section-title">
        Operational Overview
    </div>
    <div class="section-subtitle">
        Response activity across districts and apparatus
    </div>
</div>
""", unsafe_allow_html=True)
# ---------- Top Overview Charts ----------
    chart_col1, chart_col2, chart_col3 = st.columns(3)

with chart_col1:
    st.subheader("📍 Top Districts")
    st.caption("By number of incidents")

    district_counts = (
        filtered_df["District"]
        .replace("", pd.NA)
        .dropna()
        .astype(str)
        .value_counts()
        .reset_index()
    )
    district_counts.columns = ["District", "Count"]

    fig = px.bar(
        district_counts.head(10),
        x="District",
        y="Count",
        text="Count",
    )

    fig.update_traces(
        textposition="outside",
        marker_color="#ef233c"
    )

    fig.update_xaxes(type="category")

    fig.update_layout(
        height=360,
        xaxis_title="District",
        yaxis_title="Count",
        plot_bgcolor="#111827",
        paper_bgcolor="#111827",
        font=dict(color="white"),
        margin=dict(l=20, r=20, t=20, b=40),
        showlegend=False
    )

    st.plotly_chart(fig, use_container_width=True)

with chart_col2:
    st.subheader("🚒 Top Engines")
    st.caption("By number of incidents")

    engine_counts_df = (
        filtered_units_df[
            filtered_units_df["Unit"].str.startswith("E")
        ]["Unit"]
        .value_counts()
        .reset_index()
    )
    engine_counts_df.columns = ["Engine", "Count"]

    fig = px.bar(
        engine_counts_df.head(10),
        x="Engine",
        y="Count",
        text="Count",
    )

    fig.update_traces(
        textposition="outside",
        marker_color="#ff8500"
    )

    fig.update_xaxes(type="category")

    fig.update_layout(
        height=360,
        xaxis_title="Engine",
        yaxis_title="Count",
        plot_bgcolor="#111827",
        paper_bgcolor="#111827",
        font=dict(color="white"),
        margin=dict(l=20, r=20, t=20, b=40),
        showlegend=False
    )

    st.plotly_chart(fig, use_container_width=True)

with chart_col3:
    st.subheader("🚛 Top Trucks")
    st.caption("By number of responses")

    truck_counts_df = (
        filtered_units_df[
            filtered_units_df["Unit"].str.startswith("T")
        ]["Unit"]
        .value_counts()
        .reset_index()
    )
    truck_counts_df.columns = ["Truck", "Count"]

    fig = px.bar(
        truck_counts_df.head(10),
        x="Truck",
        y="Count",
        text="Count",
    )

    fig.update_traces(
        textposition="outside",
        marker_color="#1f6feb"
    )

    fig.update_xaxes(type="category")

    fig.update_layout(
        height=360,
        xaxis_title="Truck",
        yaxis_title="Count",
        plot_bgcolor="#111827",
        paper_bgcolor="#111827",
        font=dict(color="white"),
        margin=dict(l=20, r=20, t=20, b=40),
        showlegend=False
    )

    st.plotly_chart(fig, use_container_width=True)

    # ---------- Incidents Over Time ----------
st.markdown("""
<div class="section-spacing">
<div class="section-title">
    Incident Timeline
</div>
<div class="section-subtitle">
    Daily, weekly and monthly incident trends
</div>
</div>
""", unsafe_allow_html=True)

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
        plot_bgcolor="#111827",
        paper_bgcolor="#111827",
        font=dict(color="white"),
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
