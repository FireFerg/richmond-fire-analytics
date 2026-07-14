import pandas as pd
import plotly.express as px
import streamlit as st

from utils.data_loader import load_incidents


st.set_page_config(
    page_title="Districts",
    page_icon="📍",
    layout="wide",
)

st.title("📍 Districts")
st.caption("Detailed district incident and response analytics")

incidents_df, units_df = load_incidents(None)


# ---------- District Selector ----------

district_options = sorted(
    incidents_df["District"]
    .replace("", pd.NA)
    .dropna()
    .astype(str)
    .unique(),
    key=lambda value: int(value) if value.isdigit() else value
)

selected_district = st.selectbox(
    "Select District",
    district_options
)


selected_incidents_df = incidents_df[
    incidents_df["District"].astype(str) == selected_district
].copy()

selected_incident_numbers = (
    selected_incidents_df["Incident Number"]
    .dropna()
    .unique()
)

selected_units_df = units_df[
    units_df["Incident Number"].isin(selected_incident_numbers)
].copy()


# ---------- KPI Calculations ----------

total_incidents = len(selected_incidents_df)

shift_counts = (
    selected_incidents_df["Shift"]
    .replace("", pd.NA)
    .dropna()
    .value_counts()
)

top_shift = (
    shift_counts.index[0]
    if not shift_counts.empty
    else "N/A"
)

top_shift_count = (
    int(shift_counts.iloc[0])
    if not shift_counts.empty
    else 0
)


engine_counts = (
    selected_units_df[
        selected_units_df["Unit"].str.startswith("E")
    ]["Unit"]
    .value_counts()
)

top_engine = (
    engine_counts.index[0]
    if not engine_counts.empty
    else "N/A"
)

top_engine_count = (
    int(engine_counts.iloc[0])
    if not engine_counts.empty
    else 0
)


truck_counts = (
    selected_units_df[
        selected_units_df["Unit"].str.startswith("T")
    ]["Unit"]
    .value_counts()
)

top_truck = (
    truck_counts.index[0]
    if not truck_counts.empty
    else "N/A"
)

top_truck_count = (
    int(truck_counts.iloc[0])
    if not truck_counts.empty
    else 0
)


# ---------- KPI Row ----------

st.subheader(f"District {selected_district} Profile")

kpi1, kpi2, kpi3, kpi4 = st.columns(4)

kpi1.metric(
    "Total Incidents",
    total_incidents
)

kpi2.metric(
    "Top Shift",
    top_shift,
    f"{top_shift_count} incidents"
)

kpi3.metric(
    "Top Engine",
    top_engine,
    f"{top_engine_count} responses"
)

kpi4.metric(
    "Top Truck",
    top_truck,
    f"{top_truck_count} responses"
)


# ---------- Monthly and Hourly Charts ----------

chart1, chart2 = st.columns(2)

with chart1:
    monthly_incidents = (
        selected_incidents_df
        .dropna(subset=["Date"])
        .set_index("Date")
        .resample("ME")
        .size()
        .reset_index(name="Incidents")
    )

    fig = px.line(
        monthly_incidents,
        x="Date",
        y="Incidents",
        markers=True,
        title=f"District {selected_district} Incidents by Month"
    )

    fig.update_traces(
        line=dict(
            width=4,
            color="#ef233c"
        )
    )

    fig.update_layout(
        height=420,
        plot_bgcolor="#111827",
        paper_bgcolor="#111827",
        font=dict(color="white"),
        xaxis_title="Month",
        yaxis_title="Incidents",
        margin=dict(l=20, r=20, t=60, b=40)
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )


with chart2:
    hourly_incidents = (
        selected_incidents_df["Hour"]
        .dropna()
        .astype(int)
        .value_counts()
        .reindex(range(24), fill_value=0)
        .rename_axis("Hour")
        .reset_index(name="Incidents")
    )

    fig = px.bar(
        hourly_incidents,
        x="Hour",
        y="Incidents",
        text="Incidents",
        title=f"District {selected_district} Incidents by Hour"
    )

    fig.update_traces(
        marker_color="#ef233c",
        textposition="outside"
    )

    fig.update_layout(
        height=420,
        plot_bgcolor="#111827",
        paper_bgcolor="#111827",
        font=dict(color="white"),
        xaxis_title="Hour of Day",
        yaxis_title="Incidents",
        margin=dict(l=20, r=20, t=60, b=40)
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )


# ---------- Shift Breakdown ----------

st.subheader("Shift Breakdown")

shift_breakdown = (
    selected_incidents_df["Shift"]
    .replace("", "Unknown")
    .value_counts()
    .reset_index()
)

shift_breakdown.columns = [
    "Shift",
    "Incidents"
]

fig = px.bar(
    shift_breakdown,
    x="Shift",
    y="Incidents",
    text="Incidents"
)

fig.update_traces(
    marker_color="#ff8500",
    textposition="outside"
)

fig.update_layout(
    height=400,
    plot_bgcolor="#111827",
    paper_bgcolor="#111827",
    font=dict(color="white"),
    xaxis_title="Shift",
    yaxis_title="Incidents",
    margin=dict(l=20, r=20, t=20, b=40)
)

st.plotly_chart(
    fig,
    use_container_width=True
)


# ---------- Top Responding Units ----------

st.subheader("Top Responding Units")

unit_breakdown = (
    selected_units_df["Unit"]
    .value_counts()
    .reset_index()
)

unit_breakdown.columns = [
    "Unit",
    "Responses"
]

fig = px.bar(
    unit_breakdown,
    x="Unit",
    y="Responses",
    text="Responses"
)

fig.update_traces(
    marker_color="#1f6feb",
    textposition="outside"
)

fig.update_layout(
    height=450,
    plot_bgcolor="#111827",
    paper_bgcolor="#111827",
    font=dict(color="white"),
    xaxis_title="Unit",
    yaxis_title="Responses",
    margin=dict(l=20, r=20, t=20, b=40)
)

st.plotly_chart(
    fig,
    use_container_width=True
)


# ---------- Recent Incidents ----------

st.subheader("Recent Incidents")

recent_columns = [
    "Incident Number",
    "Date/Time",
    "Address",
    "Station",
    "Shift",
    "Incident Type",
    "Units"
]

recent_incidents = (
    selected_incidents_df
    .sort_values(
        "Date/Time",
        ascending=False
    )[recent_columns]
)

st.dataframe(
    recent_incidents,
    use_container_width=True,
    height=450
)