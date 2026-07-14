import pandas as pd
import plotly.express as px
import streamlit as st

from utils.data_loader import load_incidents


st.set_page_config(
    page_title="Companies",
    page_icon="🚒",
    layout="wide",
)


st.title("🚒 Companies")
st.caption("Detailed company response analytics")

incidents_df, units_df = load_incidents(None)

company_type = st.radio(
    "Company Type",
    ["Engines", "Trucks"],
    horizontal=True
)

if company_type == "Engines":
    company_df = units_df[
        units_df["Unit"].str.startswith("E")
    ].copy()

    label = "Engine"
    color = "#ff8500"

else:
    company_df = units_df[
        units_df["Unit"].str.startswith("T")
    ].copy()

    label = "Truck"
    color = "#1f6feb"

if company_df.empty:
    st.warning("No company data found.")
    st.stop()

company_options = sorted(
    company_df["Unit"]
    .dropna()
    .unique()
)

selected_company = st.selectbox(
    f"Select {label}",
    company_options
)


selected_company_df = company_df[
    company_df["Unit"] == selected_company
].copy()

if selected_company_df.empty:
    st.warning("No responses found for this company.")
    st.stop()

selected_incident_numbers = (
    selected_company_df["Incident Number"]
    .dropna()
    .unique()
)

selected_incidents_df = incidents_df[
    incidents_df["Incident Number"].isin(
        selected_incident_numbers
    )
].copy()


# ---------- KPI Calculations ----------

total_responses = len(selected_company_df)

district_counts = (
    selected_company_df["District"]
    .replace("", pd.NA)
    .dropna()
    .value_counts()
)

top_district = (
    district_counts.index[0]
    if not district_counts.empty
    else "N/A"
)

top_district_count = (
    int(district_counts.iloc[0])
    if not district_counts.empty
    else 0
)

hour_counts = (
    selected_company_df["Hour"]
    .dropna()
    .astype(int)
    .value_counts()
)

peak_hour = (
    int(hour_counts.idxmax())
    if not hour_counts.empty
    else None
)

peak_hour_display = (
    f"{peak_hour:02d}:00"
    if peak_hour is not None
    else "N/A"
)

incident_type_counts = {}

for value in selected_company_df["Incident Type"].dropna():
    for item in str(value).split(","):
        item = item.strip()

        if item:
            incident_type_counts[item] = (
                incident_type_counts.get(item, 0) + 1
            )

top_incident_type = (
    max(
        incident_type_counts,
        key=incident_type_counts.get
    )
    if incident_type_counts
    else "N/A"
)


# ---------- Company Profile ----------

st.subheader(f"{selected_company} Profile")

kpi1, kpi2, kpi3, kpi4 = st.columns(4)

kpi1.metric(
    "Total Responses",
    total_responses
)

kpi2.metric(
    "Top District",
    top_district,
    f"{top_district_count} responses"
)

kpi3.metric(
    "Peak Hour",
    peak_hour_display
)

kpi4.metric(
    "Top Incident Type",
    top_incident_type
)


# ---------- Monthly and Hourly Charts ----------

chart1, chart2 = st.columns(2)

with chart1:
    monthly_responses = (
        selected_company_df
        .dropna(subset=["Date"])
        .set_index("Date")
        .resample("ME")
        .size()
        .reset_index(name="Responses")
    )

    fig = px.line(
        monthly_responses,
        x="Date",
        y="Responses",
        markers=True,
        title=f"{selected_company} Responses by Month"
    )

    fig.update_traces(
        line=dict(
            width=4,
            color=color
        )
    )

    fig.update_layout(
        height=420,
        plot_bgcolor="#111827",
        paper_bgcolor="#111827",
        font=dict(color="white"),
        xaxis_title="Month",
        yaxis_title="Responses",
        margin=dict(l=20, r=20, t=60, b=40)
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )


with chart2:
    hourly_responses = (
        selected_company_df["Hour"]
        .dropna()
        .astype(int)
        .value_counts()
        .reindex(range(24), fill_value=0)
        .rename_axis("Hour")
        .reset_index(name="Responses")
    )

    fig = px.bar(
        hourly_responses,
        x="Hour",
        y="Responses",
        text="Responses",
        title=f"{selected_company} Responses by Hour"
    )

    fig.update_traces(
        marker_color=color,
        textposition="outside"
    )

    fig.update_layout(
        height=420,
        plot_bgcolor="#111827",
        paper_bgcolor="#111827",
        font=dict(color="white"),
        xaxis_title="Hour of Day",
        yaxis_title="Responses",
        margin=dict(l=20, r=20, t=60, b=40)
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )


# ---------- District Breakdown ----------

st.subheader("District Breakdown")

district_breakdown = (
    selected_company_df["District"]
    .replace("", pd.NA)
    .dropna()
    .value_counts()
    .reset_index()
)

district_breakdown.columns = [
    "District",
    "Responses"
]

district_breakdown["District"] = (
    district_breakdown["District"].astype(str)
)

fig = px.bar(
    district_breakdown,
    x="District",
    y="Responses",
    text="Responses"
)

fig.update_traces(
    marker_color=color,
    textposition="outside"
)

fig.update_xaxes(type="category")

fig.update_layout(
    height=450,
    plot_bgcolor="#111827",
    paper_bgcolor="#111827",
    font=dict(color="white"),
    xaxis_title="District",
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
    "District",
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