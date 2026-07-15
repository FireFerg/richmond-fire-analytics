import pandas as pd
import streamlit as st
import folium
import streamlit as st

from utils.paths import LOGO, FAVICON
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
from pathlib import Path

from utils.data_loader import load_incidents
from folium.plugins import MarkerCluster

st.set_page_config(
    page_title="Maps | RVA Fire Data",
    page_icon=str(FAVICON),
    layout="wide",
)

st.sidebar.image(
    str(LOGO),
    use_container_width=True
)

st.title("🗺️ Incident Map")
st.write("Interactive map of Richmond fire incidents.")

incidents_df, units_df = load_incidents(None)

cache_path = Path("data/geocoded_incidents.csv")


@st.cache_data
def geocode_addresses(df):
    geolocator = Nominatim(user_agent="richmond_fire_analytics")
    geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)

    rows = []

    for _, row in df.iterrows():
        address = row.get("Full Address", "")

        if not address:
            continue

        try:
            location = geocode(address)
            if location:
                rows.append({
                    "Incident Number": row["Incident Number"],
                    "Address": row["Address"],
                    "Full Address": address,
                    "Date/Time": row["Date/Time"],
                    "District": row["District"],
                    "Station": row["Station"],
                    "Shift": row["Shift"],
                    "Incident Type": row["Incident Type"],
                    "Units": row["Units"],
                    "Latitude": location.latitude,
                    "Longitude": location.longitude,
                })
        except Exception:
            pass

    return pd.DataFrame(rows)


if cache_path.exists():
    map_df = pd.read_csv(cache_path)
else:
    st.warning("First run may take a minute because addresses need to be geocoded.")
    map_df = geocode_addresses(incidents_df)
    map_df.to_csv(cache_path, index=False)

if map_df.empty:
    st.error("No geocoded incidents found.")
    st.stop()

districts = sorted(map_df["District"].dropna().astype(str).unique())
shifts = sorted(map_df["Shift"].dropna().astype(str).unique())

selected_districts = st.sidebar.multiselect("District", districts, key="map_districts")
selected_shifts = st.sidebar.multiselect("Shift", shifts, key="map_shifts")

filtered_map_df = map_df.copy()

if filtered_map_df.empty:
    st.info("No incidents match the selected filters.")
    st.stop()

if selected_districts:
    filtered_map_df = filtered_map_df[
        filtered_map_df["District"].astype(str).isin(selected_districts)
    ]

if selected_shifts:
    filtered_map_df = filtered_map_df[
        filtered_map_df["Shift"].astype(str).isin(selected_shifts)
    ]

st.metric("Mapped Incidents", len(filtered_map_df))

m = folium.Map(
    location=[37.5407, -77.4360],
    zoom_start=12,
    tiles="CartoDB dark_matter"
)

marker_cluster = MarkerCluster().add_to(m)
for _, row in filtered_map_df.iterrows():
    popup_html = f"""
    <b>{row.get("Incident Number", "")}</b><br>
    <b>Address:</b> {row.get("Address", "")}<br>
    <b>District:</b> {row.get("District", "")}<br>
    <b>Station:</b> {row.get("Station", "")}<br>
    <b>Shift:</b> {row.get("Shift", "")}<br>
    <b>Type:</b> {row.get("Incident Type", "")}<br>
    <b>Units:</b> {row.get("Units", "")}
    """

    folium.CircleMarker(
        location=[row["Latitude"], row["Longitude"]],
        radius=6,
        popup=folium.Popup(popup_html, max_width=350),
        color="#ef233c",
        fill=True,
        fill_color="#ef233c",
        fill_opacity=0.8,
    ).add_to(marker_cluster)

st_folium(m, width=None, height=700)