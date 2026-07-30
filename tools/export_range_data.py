#!/usr/bin/env python3

import argparse
import csv
import json
from pathlib import Path

from common import (
    detect_avnav_data_dir,
    get_logbuch_dir,
    get_overlays_dir,
    get_tracks_dir,
)
from exportlib.range_model import load_range


def serializable_event(event):
    result = {}

    for key, value in event.items():
        if key == "_timestamp":
            continue

        if hasattr(value, "isoformat"):
            result[key] = value.isoformat()
        else:
            result[key] = value

    return result


def write_json(path, model):
    payload = {
        "from": model["range_start_iso"],
        "to": model["range_end_iso"],
        "count": len(model["events"]),
        "include_without_position": model["include_without_position"],
        "entries": [
            serializable_event(event)
            for event in model["events"]
        ],
    }

    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def write_csv(path, model):
    fieldnames = [
        "timestamp",
        "event_type",
        "text",
        "lat",
        "lon",
        "position_source",
        "source",
        "id",
    ]

    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fieldnames,
            extrasaction="ignore",
        )
        writer.writeheader()

        for event in model["events"]:
            writer.writerow(serializable_event(event))


def main():
    parser = argparse.ArgumentParser(
        description="AVNav Logbuch Zeitraum-Rohdatenexport"
    )
    parser.add_argument("--from", dest="from_value", required=True)
    parser.add_argument("--to", dest="to_value", required=True)
    parser.add_argument(
        "--format",
        choices=("csv", "json"),
        required=True,
    )
    parser.add_argument("--avnav-data", default="")
    parser.add_argument("--output", default="")
    parser.add_argument(
        "--exclude-without-position",
        action="store_true",
    )
    args = parser.parse_args()

    avnav_data = detect_avnav_data_dir(args.avnav_data)

    model = load_range(
        get_logbuch_dir(avnav_data),
        get_tracks_dir(avnav_data),
        args.from_value,
        args.to_value,
        include_without_position=(
            not args.exclude_without_position
        ),
    )

    if not model["events"]:
        raise SystemExit("Keine Logbucheinträge im gewählten Zeitraum.")

    suffix = "." + args.format
    default_name = (
        "logbuch-"
        + model["date_compact"]
        + suffix
    )

    output = (
        Path(args.output)
        if args.output
        else get_overlays_dir(avnav_data) / default_name
    )

    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(output.suffix + ".tmp")

    if args.format == "json":
        write_json(temporary, model)
    else:
        write_csv(temporary, model)

    temporary.replace(output)

    print(f"From: {model['range_start_iso']}")
    print(f"To: {model['range_end_iso']}")
    print(f"Entries: {len(model['events'])}")
    print(f"Track points: {len(model['track_points'])}")
    print(f"Output: {output}")

    for warning in model.get("warnings") or []:
        print(f"WARNING: {warning}")


if __name__ == "__main__":
    main()
