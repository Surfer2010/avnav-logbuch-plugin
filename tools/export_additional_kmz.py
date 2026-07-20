#!/usr/bin/env python3
"""Tages-KMZ-Export auf Basis der gemeinsamen Export-Engine."""

import argparse
from pathlib import Path

from common import detect_avnav_data_dir, get_logbuch_dir, get_tracks_dir, get_overlays_dir, print_detected_paths
from exportlib.export_model import load_day, normalize_date
from exportlib.formatting import format_hms
from renderers.render_kml import render_day_kml, write_kmz


def main():
    parser = argparse.ArgumentParser(description="Export AVNav Logbuch KMZ")
    parser.add_argument("--date", default="", help="Datum als YYYY-MM-DD oder YYYYMMDD")
    parser.add_argument("--avnav-data", default="", help="AVNav Datenverzeichnis. Leer = automatisch erkennen.")
    parser.add_argument("--output", default="", help="Optionaler KMZ-Ausgabepfad")
    parser.add_argument("--dry-run", action="store_true", help="Nicht schreiben, nur prüfen")
    args = parser.parse_args()

    date_value = normalize_date(args.date or input("Welcher Tag soll erzeugt werden? [YYYY-MM-DD oder YYYYMMDD, leer=heute]: "))
    avnav_data = detect_avnav_data_dir(args.avnav_data)
    model = load_day(get_logbuch_dir(avnav_data), get_tracks_dir(avnav_data), date_value)
    output_file = Path(args.output) if args.output else get_overlays_dir(avnav_data) / f"{model['date_compact']}_logbuch.kmz"
    kml_content = render_day_kml(model)

    print_detected_paths(avnav_data)
    print(f"Date: {model['date_dash']}")
    print(f"Logbuch file: {model['logbuch_file']}")
    print(f"GPX file: {model['gpx_file']}")
    print(f"Output: {output_file}")
    print(f"Logbuch entries: {len(model['events'])}")
    print(f"Track points: {len(model['track_points'])}")
    print(f"Track segments: {len(model['segments'])}")
    print(f"Motor time: {format_hms(model['statistics']['motor']['duration_seconds'])}")
    print(f"Sail time: {format_hms(model['statistics']['sail']['duration_seconds'])}")
    for warning in model["warnings"]:
        print(warning)

    if args.dry_run:
        print("Dry run. No KMZ written.")
        return

    write_kmz(output_file, kml_content, Path(__file__).parent / "kmz-icons")
    print("KMZ written. Existing file was overwritten if present.")


if __name__ == "__main__":
    main()
