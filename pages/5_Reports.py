import streamlit as st
import folium
from streamlit_folium import st_folium

from utils.paths import LOGO, FAVICON
from utils.ui import load_css


st.set_page_config(
    page_title="Reports | RVA Fire Data",
    page_icon=str(FAVICON),
    layout="wide",
    initial_sidebar_state="expanded",
)

load_css()
st.sidebar.image(str(LOGO), use_container_width=True)

st.title("📄 Reports")
st.caption("Independent research and planning studies built from Richmond-area fire incident data.")

st.markdown(
    """
    <style>
    .report-hero {
        border: 1px solid rgba(49, 110, 230, .28);
        border-radius: 18px;
        padding: 28px 30px;
        margin: 8px 0 22px 0;
        background: linear-gradient(135deg, rgba(33,95,206,.14), rgba(33,95,206,.03));
    }
    .report-kicker {
        font-size: .82rem;
        letter-spacing: .08em;
        text-transform: uppercase;
        font-weight: 700;
        opacity: .72;
        margin-bottom: 6px;
    }
    .report-hero h2 { margin: 0 0 8px 0; font-size: 2rem; }
    .report-hero p { margin: 0; font-size: 1.05rem; line-height: 1.55; }
    .finding-card {
        border: 1px solid rgba(128,128,128,.25);
        border-radius: 14px;
        padding: 18px;
        min-height: 150px;
    }
    .finding-card h3 { margin-top: 0; }
    .small-note { opacity: .72; font-size: .9rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="report-hero">
      <div class="report-kicker">RVA Fire Data • October 2026</div>
      <h2>Richmond Fire UAS Deployment Study</h2>
      <p>
        Where should Richmond position fire-service drones? This preliminary feasibility study connects
        incident demand, fire-station geography, James River coverage, and FAA airspace constraints to
        identify promising launch-site combinations for a future Drone as First Responder program.
      </p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.info(
    "This is an independent planning study. It is not an operational recommendation, live flight briefing, "
    "or endorsement by Richmond Fire, Skydio, or the FAA."
)

st.subheader("Key findings")

c1, c2 = st.columns(2)
with c1:
    st.markdown(
        """
        <div class="finding-card">
          <h3>3-minute planning target</h3>
          <p><strong>Stations 5 · 11 · 13</strong></p>
          <p><strong>66 of 173</strong> mapped core incidents reached in the baseline model — <strong>38.2%</strong>.</p>
          <p class="small-note">Best three-station combination under the study's 35 mph / 60-second-delay baseline.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
with c2:
    st.markdown(
        """
        <div class="finding-card">
          <h3>5-minute planning target</h3>
          <p><strong>Stations 5 · 21 · 23</strong></p>
          <p><strong>149 of 173</strong> mapped core incidents reached in the baseline model — <strong>86.1%</strong>.</p>
          <p class="small-note">This wider target shifts the preferred network south and west to improve citywide reach.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("---")

st.subheader("Explore the baseline comparison")
target = st.radio(
    "Arrival target",
    options=["3 minutes", "5 minutes"],
    horizontal=True,
)

if target == "3 minutes":
    selected = ["5", "11", "13"]
    covered = 66
    pct = 38.2
    description = (
        "The shorter target rewards centrally located stations that can reach dense clusters of incidents quickly."
    )
else:
    selected = ["5", "21", "23"]
    covered = 149
    pct = 86.1
    description = (
        "At five minutes, the optimal three-site network expands south and west, producing much broader geographic coverage."
    )

m1, m2, m3, m4 = st.columns(4)
m1.metric("Recommended sites", " · ".join(selected))
m2.metric("Mapped core calls reached", f"{covered} / 173")
m3.metric("Modeled coverage", f"{pct:.1f}%")
m4.metric("Candidate incidents", "211")

st.write(description)
st.caption(
    "Baseline assumptions: 35 mph cruise speed, 60 seconds total non-travel delay, straight-line flight, "
    "core incident categories, and theoretical access to controlled airspace. These are modeled estimates, "
    "not measured response times."
)

stations = {
    "5": {"address": "324 W. Leigh St.", "lat": 37.550582399629, "lon": -77.442555896668, "airspace": "No facility-map grid at station"},
    "11": {"address": "1235 N. 28th St.", "lat": 37.537942156112, "lon": -77.408374629773, "airspace": "100 ft AGL FAA facility-map grid"},
    "13": {"address": "411 E. Commerce Rd.", "lat": 37.519338543133, "lon": -77.437699133806, "airspace": "No facility-map grid at station"},
    "21": {"address": "2505 Jefferson Davis Hwy.", "lat": 37.489068648328, "lon": -77.445152497157, "airspace": "No facility-map grid at station"},
    "23": {"address": "495 LaBrook Concourse", "lat": 37.510426010083, "lon": -77.507231811680, "airspace": "No facility-map grid at station"},
}

st.subheader("Recommended launch-site geography")
map_obj = folium.Map(
    location=[37.525, -77.455],
    zoom_start=12,
    tiles="OpenStreetMap",
)
for station_id, station in stations.items():
    active = station_id in selected
    folium.CircleMarker(
        location=[station["lat"], station["lon"]],
        radius=10 if active else 6,
        weight=3 if active else 1,
        fill=True,
        fill_opacity=.9 if active else .45,
        tooltip=f"Station {station_id} — {station['address']}",
        popup=(
            f"<b>Station {station_id}</b><br>{station['address']}<br>"
            f"{station['airspace']}<br>"
            f"{'Selected for ' + target if active else 'Alternate candidate'}"
        ),
    ).add_to(map_obj)

st_folium(map_obj, use_container_width=True, height=520, returned_objects=[])
st.caption("Larger markers show the station combination selected by the current arrival target.")

st.markdown("---")

st.subheader("What the study included")
a, b, c = st.columns(3)
with a:
    st.markdown("### Incident demand")
    st.write(
        "Seven supplied exports contained 500 rows and 494 distinct incident numbers. Classification produced "
        "211 candidate drone responses. The standard baseline used 173 mapped core incidents after exclusions "
        "and unresolved locations."
    )
with b:
    st.markdown("### Mission categories")
    st.write(
        "The core model included structure-fire activity, vehicle extrication or entrapment, and technical-rescue "
        "candidates. Hazmat incidents were modeled separately when eligibility was conditional. Elevator rescue was excluded."
    )
with c:
    st.markdown("### James River")
    st.write(
        "River coverage was evaluated independently from historical call demand using approximately 100-meter samples "
        "along the James River centerline within Richmond. Water-rescue demand data were not supplied."
    )

st.subheader("Airspace constraints")
st.write(
    "The analysis incorporated FAA Class C surface airspace, elevated Class C airspace, UAS Facility Map grids, "
    "and the downloaded national-security restriction geometry. Station 11 intersects a 100-foot AGL facility-map grid. "
    "Stations 5, 21, and 23 do not intersect the downloaded facility-map grids, although routes from those stations can "
    "still enter controlled airspace."
)
st.warning(
    "Facility-map values are planning ceilings, not flight permission. Current NOTAMs, temporary restrictions, "
    "authorization terms, BVLOS authority, weather, and other operating requirements must be checked before flight."
)

with st.expander("Method and data-quality notes", expanded=False):
    st.markdown(
        """
        **Arrival-time model**  
        Modeled arrival time = total non-travel delay + straight-line flight distance adjusted by the selected
        distance factor and cruise speed. The 60-second baseline delay represents dispatch decision, launch,
        climb, and establishment of a useful aerial view. It is an assumption, not a measured Skydio launch time.

        **Optimization**  
        Every one-, two-, and three-station combination was evaluated in the full study. The optimizer maximized
        unique eligible located incidents reached within the target and used mean geometric ETA as a tie-breaker.

        **Coordinates**  
        193 of the 211 candidate incidents were mapped. Eighteen remained unresolved. Coordinates are provisional
        and are not rooftop-verified launch or incident points.

        **Availability**  
        The model assumes an available aircraft at each selected site. It does not simulate charging, assignment
        queues, weather outages, communications failures, multiple simultaneous missions, staffing, or relief flights.
        """
    )

with st.expander("What must happen before an operational recommendation", expanded=False):
    st.markdown(
        """
        - Resolve remaining incident locations and obtain complete response-time data.
        - Validate dispatch categories and mission priorities with Richmond Fire / ECC.
        - Survey candidate sites for roof access, obstacles, power, networking, cellular/radio coverage, and security.
        - Validate realistic launch, climb, cruise, arrival, return, recharge, and maintenance times.
        - Model aircraft availability and overlapping incidents.
        - Conduct current FAA, BVLOS, and controlled-airspace authorization review.
        - Test representative routes and compare modeled times with actual flight performance.
        """
    )

st.subheader("Sources")
st.markdown(
    """
    - Richmond Fire incident exports supplied for this study
    - RVA Fire Data incident-coordinate dataset
    - City of Richmond Fire & Emergency Services station locations
    - Richmond city boundary and street-centerline data
    - USGS National Hydrography Dataset James River flowlines
    - FAA Class Airspace, UAS Facility Maps, and national-security UAS restriction data
    - Skydio public DFR planning methodology and X10 specifications
    - FAA public-safety UAS and facility-map guidance
    """
)

st.caption(
    "Version 1.0 • October 2026 • Prepared by Fergus Hughes / RVA Fire Data. "
    "All response figures shown here are modeled estimates for preliminary feasibility research."
)
