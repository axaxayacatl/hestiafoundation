
#!/usr/bin/env python3
"""Validate Hestia building-monitoring CSV exports."""

import argparse
import csv
import math
import re
import sys
from datetime import datetime
from pathlib import Path

REQUIRED_COLUMNS = {"timestamp", "sensor_id", "location"}
SENSOR_ID_PATTERN = re.compile(r"^[A-Z][A-Z0-9]*-[A-Z0-9]+$")


def validate_csv(path: Path) -> list[str]:
    errors = []

    try:
        with path.open("r", encoding="utf-8-sig", newline="") as file:
            reader = csv.DictReader(file)

            if not reader.fieldnames:
                return ["CSV is empty or has no header."]

            headers = [name.strip() for name in reader.fieldnames]
            reader.fieldnames = headers

            if len(headers) != len(set(headers)):
                errors.append("Header contains duplicate column names.")

            if any(not name for name in headers):
                errors.append("Header contains an empty column name.")

            missing = REQUIRED_COLUMNS - set(headers)
            if missing:
                return errors + [
                    "Missing required columns: "
                    + ", ".join(sorted(missing))
                ]

            for row in reader:
                line = reader.line_num

                if None in row:
                    errors.append(f"Line {line}: too many CSV fields.")
                    continue

                row = {
                    key.strip(): (value or "").strip()
                    for key, value in row.items()
                    if key is not None
                }

                if all(not value for value in row.values()):
                    continue

                timestamp = row.get("timestamp", "")
                try:
                    datetime.fromisoformat(
                        timestamp.replace("Z", "+00:00")
                    )
                except ValueError:
                    errors.append(
                        f"Line {line}: invalid ISO 8601 timestamp."
                    )

                sensor_id = row.get("sensor_id", "")
                if not SENSOR_ID_PATTERN.fullmatch(sensor_id):
                    errors.append(
                        f"Line {line}: invalid sensor_id {sensor_id!r}."
                    )

                if not row.get("location", ""):
                    errors.append(f"Line {line}: location is required.")

                for column, value in row.items():
                    if column in REQUIRED_COLUMNS or not value:
                        continue

                    if column.endswith(("_c", "_pct")):
                        try:
                            number = float(value)
                            if not math.isfinite(number):
                                raise ValueError
                        except ValueError:
                            errors.append(
                                f"Line {line}: {column} must be a "
                                "finite number when provided."
                            )

    except OSError as exc:
        return [f"Could not read {path}: {exc}"]
    except csv.Error as exc:
        return [f"CSV parsing error: {exc}"]

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate Hestia building-monitoring CSV data."
    )
    parser.add_argument("csv_file", type=Path, help="CSV file to validate")
    args = parser.parse_args()

    errors = validate_csv(args.csv_file)

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print(f"Valid CSV: {args.csv_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
