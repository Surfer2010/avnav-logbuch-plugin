#!/usr/bin/env python3
"""Create a self-contained daily HTML report."""

import argparse
from pathlib import Path

from common import detect_avnav_data_dir, get_logbuch_dir, get_tracks_dir, get_overlays_dir, print_detected_paths
from exportlib.export_model import load_day, normalize_date
from renderers.render_daily_html import render_daily_html


def main():
    parser = argparse.ArgumentParser(description="Export AVNav Logbuch HTML-Tagesbericht")
    parser.add_argument("--date", default="", help="Datum als YYYY-MM-DD oder YYYYMMDD")
    parser.add_argument("--avnav-data", default="", help="AVNav Datenverzeichnis")
    parser.add_argument("--output", default="", help="Optionaler HTML-Ausgabepfad")
    parser.add_argument("--offline-map", action="store_true", help="Keine Online-Kartenkacheln abrufen")
    parser.add_argument("--chart-xml", default="", help="Optionale AVNav XML-Kartendefinition")
    parser.add_argument("--cache-dir", default="", help="Optionales Kartenkachel-Cacheverzeichnis")
    args = parser.parse_args()

    day = normalize_date(args.date)
    avnav_data = detect_avnav_data_dir(args.avnav_data)
    model = load_day(get_logbuch_dir(avnav_data), get_tracks_dir(avnav_data), day)
    output = Path(args.output) if args.output else get_overlays_dir(avnav_data) / f"{model['date_compact']}_logbuch.html"
    chart_xml = Path(args.chart_xml) if args.chart_xml else Path(avnav_data) / "charts" / "osm-online.xml"
    cache_dir = Path(args.cache_dir) if args.cache_dir else Path(avnav_data) / "logbuch" / "map-cache"

    content = render_daily_html(
        model,
        online_map=not args.offline_map,
        cache_dir=cache_dir,
        chart_xml=chart_xml,
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(output.suffix + ".tmp")
    temporary.write_text(content, encoding="utf-8")
    temporary.replace(output)

    print_detected_paths(avnav_data)
    print(f"Date: {model['date_dash']}")
    print(f"Output: {output}")
    print(f"HTML bytes: {output.stat().st_size}")
    print(f"Online map: {not args.offline_map}")
    for warning in model.get("warnings") or []:
        print(warning)
    print("HTML report written.")


if __name__ == "__main__":
    main()
