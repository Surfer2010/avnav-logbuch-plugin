#!/usr/bin/env python3
"""Mehrtag-/Törn-KMZ-Export auf Basis der gemeinsamen Export-Engine."""

import argparse
from datetime import timedelta
from pathlib import Path

from common import detect_avnav_data_dir, get_logbuch_dir, get_tracks_dir, get_overlays_dir, print_detected_paths
from exportlib.export_model import combine_statistics, load_day, normalize_date
from exportlib.formatting import format_hms
from renderers.render_kml import render_trip_kml, write_kmz


def daterange(start, end):
    current = start
    while current <= end:
        yield current
        current += timedelta(days=1)


def main():
    parser = argparse.ArgumentParser(description="Export AVNav Törn KMZ")
    parser.add_argument("--from-date", required=True)
    parser.add_argument("--to-date", required=True)
    parser.add_argument("--avnav-data", default="")
    parser.add_argument("--output", default="")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    start_date = normalize_date(args.from_date)
    end_date = normalize_date(args.to_date)
    if end_date < start_date:
        raise SystemExit("Enddatum liegt vor Startdatum.")

    avnav_data = detect_avnav_data_dir(args.avnav_data)
    logbuch_dir = get_logbuch_dir(avnav_data)
    tracks_dir = get_tracks_dir(avnav_data)
    models = []
    warnings = []
    print_detected_paths(avnav_data)

    for day in daterange(start_date, end_date):
        try:
            model = load_day(logbuch_dir, tracks_dir, day)
        except FileNotFoundError as error:
            print(f"SKIP: {error}")
            continue
        models.append(model)
        warnings.extend(f"{model['date_dash']}: {warning}" for warning in model["warnings"])
        print(f"DAY: {model['date_dash']} entries={len(model['events'])} points={len(model['track_points'])}")

    total_stats = combine_statistics(models)
    start_dash = start_date.strftime("%Y-%m-%d")
    end_dash = end_date.strftime("%Y-%m-%d")
    output_file = Path(args.output) if args.output else get_overlays_dir(avnav_data) / f"{start_date:%Y%m%d}-{end_date:%Y%m%d}_toern_logbuch.kmz"
    kml_content = render_trip_kml(start_dash, end_dash, models, total_stats)

    print(f"Output: {output_file}")
    print(f"Days included: {len(models)}")
    print(f"Motor time: {format_hms(total_stats['motor']['duration_seconds'])}")
    print(f"Sail time: {format_hms(total_stats['sail']['duration_seconds'])}")
    for warning in warnings:
        print(warning)

    if args.dry_run:
        print("Dry run. No KMZ written.")
        return

    write_kmz(output_file, kml_content, Path(__file__).parent / "kmz-icons")
    print("Trip KMZ written. Existing file was overwritten if present.")


if __name__ == "__main__":
    main()
