import csv
import json
import shutil
from datetime import datetime
from pathlib import Path

from geopy.extra.rate_limiter import RateLimiter
from geopy.geocoders import Nominatim


MASTER_FILE = Path("data/Incidents.txt")
NEW_FILE = Path("data/new_incidents.txt")
GEOCODED_FILE = Path("data/geocoded_incidents.csv")

CSV_FIELDS = [
    "Incident Number",
    "Address",
    "Full Address",
    "Date/Time",
    "District",
    "Station",
    "Shift",
    "Incident Type",
    "Units",
    "Latitude",
    "Longitude",
]


def load_json_file(path):
    raw = path.read_text(encoding="utf-8", errors="ignore")
    return json.loads(raw)


def get_incidents(data):
    if isinstance(data, dict) and "incidents" in data:
        return data["incidents"]

    if isinstance(data, list):
        return data

    raise ValueError("Could not find incidents list in file.")


def value_as_text(value):
    """Convert strings, lists, or other values into clean CSV text."""
    if value is None:
        return ""

    if isinstance(value, list):
        return ", ".join(str(item) for item in value if item is not None)

    return str(value).strip()


def get_incident_type(incident):
    """
    Supports several possible source-field names.
    Adjust this list later if your raw JSON uses another field.
    """
    for field in (
        "incidentType",
        "incidentTypes",
        "types",
        "type",
        "cadLatestSubmission",
    ):
        value = incident.get(field)

        if value:
            return value_as_text(value)

    return ""


def get_units(incident):
    for field in ("units", "unit"):
        value = incident.get(field)

        if value:
            return value_as_text(value)

    return ""


def create_full_address(address):
    address = value_as_text(address)

    if not address:
        return ""

    if "richmond" in address.lower():
        return address

    return f"{address}, Richmond, VA"


def load_existing_geocoded_rows():
    if not GEOCODED_FILE.exists():
        return []

    with GEOCODED_FILE.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as csv_file:
        return list(csv.DictReader(csv_file))


def build_coordinate_cache(existing_rows):
    """
    Maps a normalized full address to previously saved coordinates.

    This prevents repeated geocoding when multiple incidents occur
    at the same address.
    """
    coordinate_cache = {}

    for row in existing_rows:
        full_address = value_as_text(row.get("Full Address")).lower()
        latitude = value_as_text(row.get("Latitude"))
        longitude = value_as_text(row.get("Longitude"))

        if full_address and latitude and longitude:
            coordinate_cache[full_address] = (latitude, longitude)

    return coordinate_cache


def get_existing_geocoded_incident_numbers(existing_rows):
    return {
        value_as_text(row.get("Incident Number"))
        for row in existing_rows
        if value_as_text(row.get("Incident Number"))
    }


def geocode_new_incidents(new_incidents):
    existing_rows = load_existing_geocoded_rows()

    existing_map_incidents = get_existing_geocoded_incident_numbers(
        existing_rows
    )
    coordinate_cache = build_coordinate_cache(existing_rows)

    geolocator = Nominatim(
        user_agent="rva-fire-data-incident-map"
    )

    geocode = RateLimiter(
        geolocator.geocode,
        min_delay_seconds=1,
        max_retries=2,
        error_wait_seconds=5,
        swallow_exceptions=True,
    )

    rows_to_append = []
    failed_incidents = []

    for incident in new_incidents:
        incident_number = value_as_text(
            incident.get("incidentNumber")
        )

        if not incident_number:
            continue

        if incident_number in existing_map_incidents:
            print(
                f"Skipping {incident_number}: already exists in map CSV."
            )
            continue

        address = value_as_text(
            incident.get("streetAddress")
        )
        full_address = create_full_address(address)

        if not full_address:
            print(
                f"Skipping {incident_number}: no street address."
            )
            failed_incidents.append(
                (incident_number, "Missing address")
            )
            continue

        normalized_address = full_address.lower()

        if normalized_address in coordinate_cache:
            latitude, longitude = coordinate_cache[
                normalized_address
            ]

            print(
                f"Reused coordinates for {incident_number}: "
                f"{full_address}"
            )

        else:
            print(
                f"Geocoding {incident_number}: {full_address}"
            )

            location = geocode(
                full_address,
                exactly_one=True,
                country_codes="us",
            )

            if location is None:
                print(
                    f"Could not geocode {incident_number}: "
                    f"{full_address}"
                )
                failed_incidents.append(
                    (incident_number, full_address)
                )
                continue

            latitude = location.latitude
            longitude = location.longitude

            coordinate_cache[normalized_address] = (
                latitude,
                longitude,
            )

        row = {
            "Incident Number": incident_number,
            "Address": address,
            "Full Address": full_address,
            "Date/Time": value_as_text(
                incident.get("incidentOnsetDateTime")
            ),
            "District": value_as_text(
                incident.get("district")
            ),
            "Station": value_as_text(
                incident.get("station")
            ),
            "Shift": value_as_text(
                incident.get("shift")
            ),
            "Incident Type": get_incident_type(incident),
            "Units": get_units(incident),
            "Latitude": latitude,
            "Longitude": longitude,
        }

        rows_to_append.append(row)

    return rows_to_append, failed_incidents


def append_geocoded_rows(rows):
    if not rows:
        return

    GEOCODED_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    file_exists = GEOCODED_FILE.exists()
    file_has_content = (
        file_exists and GEOCODED_FILE.stat().st_size > 0
    )

    with GEOCODED_FILE.open(
        "a",
        encoding="utf-8",
        newline="",
    ) as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=CSV_FIELDS,
        )

        if not file_has_content:
            writer.writeheader()

        writer.writerows(rows)


def save_master_data(master_data, master_incidents):
    master_incidents.sort(
        key=lambda incident: incident.get(
            "incidentOnsetDateTime",
            "",
        ),
        reverse=True,
    )

    if isinstance(master_data, dict):
        master_data["incidents"] = master_incidents
        master_data["totalCount"] = len(master_incidents)
        output_data = master_data
    else:
        output_data = master_incidents

    MASTER_FILE.write_text(
        json.dumps(output_data, indent=4),
        encoding="utf-8",
    )


def main():
    if not MASTER_FILE.exists():
        raise FileNotFoundError(
            f"Master file not found: {MASTER_FILE}"
        )

    if not NEW_FILE.exists():
        raise FileNotFoundError(
            f"New incident file not found: {NEW_FILE}"
        )

    master_data = load_json_file(MASTER_FILE)
    new_data = load_json_file(NEW_FILE)

    master_incidents = get_incidents(master_data)
    new_incidents = get_incidents(new_data)

    existing_numbers = {
        incident.get("incidentNumber")
        for incident in master_incidents
        if incident.get("incidentNumber")
    }

    new_unique_incidents = []
    duplicate_count = 0

    for incident in new_incidents:
        incident_number = incident.get("incidentNumber")

        if not incident_number:
            continue

        if incident_number in existing_numbers:
            duplicate_count += 1
        else:
            new_unique_incidents.append(incident)
            existing_numbers.add(incident_number)

    print("\nIncident Merge Preview")
    print("----------------------")
    print(f"Master incidents:     {len(master_incidents)}")
    print(f"New export incidents: {len(new_incidents)}")
    print(f"Already existed:      {duplicate_count}")
    print(f"New incidents:        {len(new_unique_incidents)}")
    print(
        f"Total after merge:    "
        f"{len(master_incidents) + len(new_unique_incidents)}"
    )

    if not new_unique_incidents:
        print("\nNo new incidents to add.")
        return

    confirm = input(
        "\nProceed with merge and map update? "
        "Type Y to continue: "
    ).strip().upper()

    if confirm != "Y":
        print("Update cancelled. No files were changed.")
        return

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    incident_backup = Path(
        f"data/Incidents_backup_{timestamp}.txt"
    )
    shutil.copy(MASTER_FILE, incident_backup)

    geocoded_backup = None

    if GEOCODED_FILE.exists():
        geocoded_backup = Path(
            f"data/geocoded_incidents_backup_{timestamp}.csv"
        )
        shutil.copy(GEOCODED_FILE, geocoded_backup)

    print("\nUpdating map coordinates...")
    map_rows, failed_incidents = geocode_new_incidents(
        new_unique_incidents
    )

    master_incidents.extend(new_unique_incidents)
    save_master_data(master_data, master_incidents)
    append_geocoded_rows(map_rows)

    print("\nUpdate complete.")
    print(f"Incident backup: {incident_backup}")

    if geocoded_backup:
        print(f"Map backup:      {geocoded_backup}")

    print(
        f"New incidents added: "
        f"{len(new_unique_incidents)}"
    )
    print(
        f"New map rows added:  "
        f"{len(map_rows)}"
    )
    print(
        f"Total incidents now: "
        f"{len(master_incidents)}"
    )

    if failed_incidents:
        print("\nMap locations not added:")
        for incident_number, reason in failed_incidents:
            print(f"- {incident_number}: {reason}")

        print(
            "\nThese incidents remain in Incidents.txt, "
            "but they will not appear on the map until their "
            "addresses are geocoded."
        )


if __name__ == "__main__":
    main()