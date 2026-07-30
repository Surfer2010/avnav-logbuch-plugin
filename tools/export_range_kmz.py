#!/usr/bin/env python3
"""Create a KMZ export for an exact time range."""

import argparse
from pathlib import Path

from common import (
    detect_avnav_data_dir,
    get_logbuch_dir,
    get_overlays_dir,
    get_tracks_dir,
)
from exportlib.range_model import load_range
from renderers.render_kml import render_trip_kml, write_kmz


def main():
    parser = argparse.ArgumentParser(
        description="AVNav Logbuch KMZ-Zeitraumexport"
    )
    parser.add_argument("--from", dest="from_value", required=True)
    parser.add_argument("--to", dest="to_value", required=True)
    parser.add_argument("--avnav-data", default="")
    parser.add_argument("--output", default="")
    parser.add_argument(
        "--exclude-without-position",
        action="store_true",
    )
    parser.add_argument("--dry-run", action="store_true")
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
        raise SystemExit(
            "Keine Logbucheinträge im gewählten Zeitraum."
        )

    start_label = model["range_start"].strftime(
        "%Y-%m-%d %H:%M"
    )
    end_label = model["range_end"].strftime(
        "%Y-%m-%d %H:%M"
    )

    output = (
        Path(args.output)
        if args.output
        else (
            get_overlays_dir(avnav_data)
            / f"logbuch-{model['date_compact']}.kmz"
        )
    )

    kml_content = render_trip_kml(
        start_label,
        end_label,
        [model],
        model["statistics"],
    )

    print(f"From: {model['range_start_iso']}")
    print(f"To: {model['range_end_iso']}")
    print(f"Entries: {len(model['events'])}")
    print(f"Track points: {len(model['track_points'])}")
    print(f"Output: {output}")

    for warning in model.get("warnings") or []:
        print(f"WARNING: {warning}")

    if args.dry_run:
        print("Dry run. No KMZ written.")
        return

    write_kmz(
        output,
        kml_content,
        Path(__file__).parent / "kmz-icons",
    )

    print("Range KMZ written.")


if __name__ == "__main__":
    main()
