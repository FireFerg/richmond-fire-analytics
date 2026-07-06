# Richmond Fire Analytics Dashboard

This is a Streamlit dashboard for analyzing Richmond Fire incident exports.

## What it does

- Loads your `Incidents.txt` / JSON export
- Creates KPI cards
- Filters by district, shift, station, unit, and incident type
- Shows unit frequency
- Shows district and shift breakdowns
- Shows incident trends over time
- Creates a Google My Maps CSV export

## How to run it locally

### 1. Install Python

Install Python 3.11 or newer.

### 2. Open this folder in Terminal / PowerShell

```bash
cd richmond_fire_dashboard_project
```

### 3. Install requirements

```bash
pip install -r requirements.txt
```

### 4. Run the dashboard

```bash
streamlit run app.py
```

Then open the local URL Streamlit gives you.

On Windows, you can also double-click:

```text
run_dashboard_windows.bat
```

## How to use with new exports

You have two options:

1. Replace `data/Incidents.txt` with a new export, then restart the dashboard.
2. Use the upload box in the dashboard sidebar.

## Google My Maps

Inside the dashboard, go to the **Map Export** tab and download the map CSV.

Then:
1. Go to `mymaps.google.com`
2. Create a new map
3. Import the CSV
4. Choose `Full Address` as the location field
5. Choose `Name` as the marker title

## Next upgrades

- Add geocoded latitude/longitude
- Add interactive map inside the dashboard
- Add heat map
- Add station location layer
- Add n8n automation
- Add GitHub Actions or scheduled processing
