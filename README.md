# Richmond Fire Analytics Project

This starter project turns a Richmond Fire incident export into analysis-ready files.

## Files Included

- `richmond_fire_analytics_workbook.xlsx`  
  Excel/Google Sheets workbook with dashboard and analysis tabs.

- `google_my_maps_import.csv`  
  Upload this directly into Google My Maps.

- `master_incidents.csv`  
  One row per incident.

- `unit_frequency.csv`  
  Count of each apparatus/unit.

- `district_frequency.csv`  
  Count by district.

- `shift_frequency.csv`  
  Count by A/B/C shift.

- `station_frequency.csv`  
  Count by listed station.

- `incident_type_frequency.csv`  
  Count by incident type tag.

- `district_by_shift.csv`  
  District incidents split by A/B/C shift.

- `unit_by_shift.csv`  
  Unit responses split by A/B/C shift.

- `missing_shift_incidents.csv`  
  Incidents with no `shift` field in the export.

- `richmond_fire_analyzer.py`  
  Reusable Python script for future exports.

## How to Use Google My Maps

1. Go to https://mymaps.google.com
2. Click **Create a New Map**
3. Click **Import**
4. Upload `google_my_maps_import.csv`
5. Choose **Full Address** as the location column
6. Choose **Name** as the marker title
7. Style by **District**, **Shift**, or **Incident Type**

## How to Run the Script Locally

Install Python 3, then run:

```bash
python richmond_fire_analyzer.py Incidents.txt output
```

The script uses only the Python standard library.

## Recommended GitHub Repo Structure

```text
richmond-fire-analytics/
├── data/
│   └── Incidents.txt
├── output/
│   └── generated CSV files
├── richmond_fire_analyzer.py
└── README.md
```

## Next Upgrades

- Add geocoded latitude/longitude
- Add heat map layer
- Add station locations
- Add filters by unit, district, and shift
- Add monthly trend charts
- Connect to n8n for automatic file processing
