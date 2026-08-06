#!/usr/bin/env python3
"""Create a self-contained HTML report for an exact time range."""

import argparse
from pathlib import Path

from common import (
    detect_avnav_data_dir,
    get_logbuch_dir,
    get_overlays_dir,
    get_tracks_dir,
)
from exportlib.range_model import load_range
from renderers.render_daily_html import render_daily_html


def main():
    parser = argparse.ArgumentParser(
        description="AVNav Logbuch HTML-Zeitraumbericht"
    )
    parser.add_argument("--from", dest="from_value", required=True)
    parser.add_argument("--to", dest="to_value", required=True)
    parser.add_argument("--avnav-data", default="")
    parser.add_argument("--output", default="")
    parser.add_argument(
        "--without-map",
        action="store_true",
        help="Keine Trackkarte in den HTML-Bericht einfügen",
    )
    parser.add_argument(
        "--offline-map",
        action="store_true",
        help="Keine Online-Kartenkacheln abrufen",
    )
    parser.add_argument("--chart-xml", default="")
    parser.add_argument("--cache-dir", default="")
    args = parser.parse_args()

    avnav_data = detect_avnav_data_dir(args.avnav_data)

    model = load_range(
        get_logbuch_dir(avnav_data),
        get_tracks_dir(avnav_data),
        args.from_value,
        args.to_value,
        include_without_position=True,
    )

    if not model["events"]:
        raise SystemExit(
            "Keine Logbucheinträge im gewählten Zeitraum."
        )

    title = (
        "Logbuch – Zeitraum "
        + model["range_start_label"]
        + " bis "
        + model["range_end_label"]
    )

    output = (
        Path(args.output)
        if args.output
        else (
            get_overlays_dir(avnav_data)
            / f"logbuch-{model['date_compact']}.html"
        )
    )

    chart_xml = (
        Path(args.chart_xml)
        if args.chart_xml
        else Path(avnav_data) / "charts" / "osm-online.xml"
    )

    cache_dir = (
        Path(args.cache_dir)
        if args.cache_dir
        else Path(avnav_data) / "logbuch" / "map-cache"
    )

    content = render_daily_html(
        model,
        title=title,
        include_map=not args.without_map,
        online_map=not args.offline_map,
        chart_xml=chart_xml,
        cache_dir=cache_dir,
    )

    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(output.suffix + ".tmp")
    temporary.write_text(content, encoding="utf-8")
    temporary.replace(output)

    print(f"From: {model['range_start_iso']}")
    print(f"To: {model['range_end_iso']}")
    print(f"Entries: {len(model['events'])}")
    print(f"Track points: {len(model['track_points'])}")
    print(f"Map included: {not args.without_map}")
    print(f"Output: {output}")

    for warning in model.get("warnings") or []:
        print(f"WARNING: {warning}")


if __name__ == "__main__":
    main()
