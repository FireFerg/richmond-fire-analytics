import json
import shutil
from pathlib import Path
from datetime import datetime


MASTER_FILE = Path("data/Incidents.txt")
NEW_FILE = Path("data/new_incidents.txt")


def load_json_file(path):
    raw = path.read_text(encoding="utf-8", errors="ignore")
    return json.loads(raw)


def get_incidents(data):
    if isinstance(data, dict) and "incidents" in data:
        return data["incidents"]

    if isinstance(data, list):
        return data

    raise ValueError("Could not find incidents list in file.")


def main():
    if not MASTER_FILE.exists():
        raise FileNotFoundError(f"Master file not found: {MASTER_FILE}")

    if not NEW_FILE.exists():
        raise FileNotFoundError(f"New incident file not found: {NEW_FILE}")

    master_data = load_json_file(MASTER_FILE)
    new_data = load_json_file(NEW_FILE)

    master_incidents = get_incidents(master_data)
    new_incidents = get_incidents(new_data)

    existing_numbers = {
        inc.get("incidentNumber")
        for inc in master_incidents
        if inc.get("incidentNumber")
    }

    new_unique_incidents = []
    duplicate_count = 0

    for inc in new_incidents:
        incident_number = inc.get("incidentNumber")

        if not incident_number:
            continue

        if incident_number in existing_numbers:
            duplicate_count += 1
        else:
            new_unique_incidents.append(inc)

    print("\nIncident Merge Preview")
    print("----------------------")
    print(f"Master incidents:     {len(master_incidents)}")
    print(f"New export incidents: {len(new_incidents)}")
    print(f"Already existed:      {duplicate_count}")
    print(f"New incidents:        {len(new_unique_incidents)}")
    print(f"Total after merge:    {len(master_incidents) + len(new_unique_incidents)}")

    if not new_unique_incidents:
        print("\nNo new incidents to add.")
        return

    confirm = input("\nProceed with merge? Type Y to continue: ").strip().upper()

    if confirm != "Y":
        print("Merge cancelled. No files were changed.")
        return

    backup_file = Path(
        f"data/Incidents_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    )
    shutil.copy(MASTER_FILE, backup_file)

    master_incidents.extend(new_unique_incidents)

    master_incidents.sort(
        key=lambda x: x.get("incidentOnsetDateTime", ""),
        reverse=True
    )

    if isinstance(master_data, dict):
        master_data["incidents"] = master_incidents
        master_data["totalCount"] = len(master_incidents)
        output_data = master_data
    else:
        output_data = master_incidents

    MASTER_FILE.write_text(
        json.dumps(output_data, indent=4),
        encoding="utf-8"
    )

    print("\nMerge complete.")
    print(f"Backup created: {backup_file}")
    print(f"New incidents added: {len(new_unique_incidents)}")
    print(f"Total incidents now: {len(master_incidents)}")


if __name__ == "__main__":
    main()