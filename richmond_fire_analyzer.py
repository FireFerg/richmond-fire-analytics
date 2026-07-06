#!/usr/bin/env python3
"""
Richmond Fire Incident Analyzer

Usage:
    python richmond_fire_analyzer.py Incidents.txt output_folder

This script reads a JSON/text export containing an "incidents" array and produces CSV files for:
- master incidents
- Google My Maps import
- unit frequency
- district frequency
- shift frequency
- station frequency
- incident type frequency
- district by shift
- unit by shift
- missing shift incidents

It uses only the Python standard library.
"""

import csv
import json
import sys
from pathlib import Path
from collections import Counter, defaultdict
from datetime import datetime

def split_units(units):
    return [u.strip() for u in (units or "").split(",") if u.strip()]

def parse_dt(dt_str):
    if not dt_str:
        return "", "", ""
    try:
        dt = datetime.fromisoformat(dt_str)
        return dt.strftime("%Y-%m-%d %H:%M:%S"), dt.date().isoformat(), dt.strftime("%H:%M:%S")
    except Exception:
        return dt_str, "", ""

def sorted_items(counter):
    return sorted(counter.items(), key=lambda x: (-x[1], str(x[0])))

def write_csv(path, headers, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)

def analyze(input_path, output_dir):
    input_path = Path(input_path)
    output_dir = Path(output_dir)
    data = json.loads(input_path.read_text(errors="ignore"))
    incidents = data.get("incidents", [])

    master_headers = [
        "Incident ID", "Incident Number", "Date/Time", "Date", "Time",
        "Address", "Full Address", "District", "Station", "Shift", "Zone",
        "Incident Type", "Units", "Unit Count", "Report Writer",
        "CAD Latest Submission", "Submission Status Type ID"
    ]

    master_rows = []
    unit_counter = Counter()
    district_counter = Counter()
    shift_counter = Counter()
    station_counter = Counter()
    type_counter = Counter()
    district_shift = defaultdict(Counter)
    unit_shift = defaultdict(Counter)
    missing_shift_rows = []

    for inc in incidents:
        dt_val, date_val, time_val = parse_dt(inc.get("incidentOnsetDateTime", ""))
        addr = inc.get("streetAddress", "") or ""
        full_addr = f"{addr}, Richmond, VA" if addr else ""
        district = str(inc.get("district", "") or "").strip()
        shift = str(inc.get("shift", "") or "").strip()
        station = str(inc.get("station", "") or "").strip()
        typ = str(inc.get("types", "") or "").strip()
        units = inc.get("units", "") or ""
        units_list = split_units(units)

        for u in units_list:
            unit_counter[u] += 1
            if shift:
                unit_shift[u][shift] += 1

        if district:
            district_counter[district] += 1
            if shift:
                district_shift[district][shift] += 1
        if shift:
            shift_counter[shift] += 1
        else:
            missing_shift_rows.append([inc.get("incidentNumber",""), dt_val, addr, district, station, typ, units])
        if station:
            station_counter[station] += 1
        if typ:
            for t in [x.strip() for x in typ.split(",") if x.strip()]:
                type_counter[t] += 1

        master_rows.append([
            inc.get("incidentId", ""),
            inc.get("incidentNumber", ""),
            dt_val,
            date_val,
            time_val,
            addr,
            full_addr,
            district,
            station,
            shift,
            inc.get("zone", ""),
            typ,
            units,
            len(units_list),
            inc.get("reportWriter", ""),
            inc.get("cadLatestSubmission", ""),
            inc.get("incidentSubmissionStatusTypeId", "")
        ])

    write_csv(output_dir / "master_incidents.csv", master_headers, master_rows)

    map_headers = ["Name", "Address", "Full Address", "Date/Time", "District", "Station", "Shift", "Incident Type", "Units"]
    map_rows = [[r[1], r[5], r[6], r[2], r[7], r[8], r[9], r[11], r[12]] for r in master_rows if r[5]]
    write_csv(output_dir / "google_my_maps_import.csv", map_headers, map_rows)

    write_csv(output_dir / "unit_frequency.csv", ["Unit", "Frequency"], sorted_items(unit_counter))
    write_csv(output_dir / "district_frequency.csv", ["District", "Frequency"], sorted_items(district_counter))
    write_csv(output_dir / "shift_frequency.csv", ["Shift", "Frequency"], sorted_items(shift_counter))
    write_csv(output_dir / "station_frequency.csv", ["Station", "Frequency"], sorted_items(station_counter))
    write_csv(output_dir / "incident_type_frequency.csv", ["Incident Type", "Frequency"], sorted_items(type_counter))

    district_shift_rows = []
    for d, total in sorted_items(district_counter):
        counted = sum(district_shift[d].values())
        district_shift_rows.append([d, district_shift[d].get("A Shift", 0), district_shift[d].get("B Shift", 0), district_shift[d].get("C Shift", 0), total-counted, total])
    write_csv(output_dir / "district_by_shift.csv", ["District", "A Shift", "B Shift", "C Shift", "No Shift", "Total"], district_shift_rows)

    unit_shift_rows = []
    for u, total in sorted_items(unit_counter):
        counted = sum(unit_shift[u].values())
        unit_shift_rows.append([u, unit_shift[u].get("A Shift", 0), unit_shift[u].get("B Shift", 0), unit_shift[u].get("C Shift", 0), total-counted, total])
    write_csv(output_dir / "unit_by_shift.csv", ["Unit", "A Shift", "B Shift", "C Shift", "No Shift", "Total"], unit_shift_rows)

    write_csv(output_dir / "missing_shift_incidents.csv", ["Incident Number", "Date/Time", "Address", "District", "Station", "Incident Type", "Units"], missing_shift_rows)

    print(f"Processed {len(incidents)} incidents.")
    print(f"Created CSV outputs in: {output_dir}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python richmond_fire_analyzer.py Incidents.txt output_folder")
        sys.exit(1)
    analyze(sys.argv[1], sys.argv[2])
