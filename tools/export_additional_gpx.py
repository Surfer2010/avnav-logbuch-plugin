#!/usr/bin/env python3
"""
Export additional GPX overlays for AVNav.

Creates one daily GPX file:

    YYYY-MM-DD_additional.gpx

The file contains:
- one or more motor track segments
- one or more sail track segments
- anchor waypoints

Input:
- AVNav track file:   tracks/YYYY-MM-DD.avt
- Logbuch JSONL:      logbuch/logbuch-YYYY-MM-DD.jsonl

Example:

    python3 tools/export_additional_gpx.py --date 2026-05-21 --avnav-data /home/pi/avnav/data
"""

import argparse
import html
import json
from datetime import datetime
from pathlib import Path


START_EVENTS = {
    "motor_on": "motor",
    "sail_set": "sail",
    "anchor_down": "anchor",
}

END_EVENTS = {
    "motor_off": "motor",
    "sail_down": "sail",
    "anchor_up": "anchor",
}

DISPLAY_NAMES = {
    "motor": "Motor",
    "sail": "Segel",
    "anchor": "Anker",
}


def parse_time(value):
    if not value:
        return None

    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def read_logbuch(path):
    entries = []

    if not path.exists():
        raise FileNotFoundError(f"Logbuch file not found: {path}")

    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            line = line.strip()

            if not line:
                continue

            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                print(f"WARNING: invalid JSON in {path}:{line_number}")
                continue

            timestamp = parse_time(entry.get("timestamp"))

            if timestamp is None:
                print(f"WARNING: invalid timestamp in {path}:{line_number}")
                continue

            entry["_timestamp"] = timestamp
            entries.append(entry)

    entries.sort(key=lambda item: item["_timestamp"])
    return entries


def read_avt(path):
    points = []

    if not path.exists():
        raise FileNotFoundError(f"AVT track file not found: {path}")

    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            line = line.strip()

            if not line or line.startswith("#"):
                continue

            parts = line.split(",")

            if len(parts) < 5:
                print(f"WARNING: invalid AVT line in {path}:{line_number}")
                continue

            timestamp = parse_time(parts[0])

            if timestamp is None:
                print(f"WARNING: invalid AVT timestamp in {path}:{line_number}")
                continue

            try:
                point = {
                    "timestamp": timestamp,
                    "time": parts[0],
                    "lat": float(parts[1]),
                    "lon": float(parts[2]),
                    "course": float(parts[3]),
                    "speed": float(parts[4]),
                    "distance": float(parts[5]) if len(parts) > 5 else None,
                }
            except ValueError:
                print(f"WARNING: invalid AVT numeric value in {path}:{line_number}")
                continue

            points.append(point)

    points.sort(key=lambda item: item["timestamp"])
    return points


def build_intervals(entries):
    open_states = {
        "motor": None,
        "sail": None,
        "anchor": None,
    }

    intervals = []
    anchors = []
    warnings = []

    for entry in entries:
        event_type = entry.get("event_type")

        if event_type in START_EVENTS:
            state_name = START_EVENTS[event_type]

            if state_name == "anchor":
                anchors.append(entry)

            if open_states[state_name] is not None:
                warnings.append(
                    f"WARNING: {state_name} already open at {entry.get('timestamp')}"
                )

            open_states[state_name] = entry

        elif event_type in END_EVENTS:
            state_name = END_EVENTS[event_type]
            start_entry = open_states[state_name]

            if start_entry is None:
                warnings.append(
                    f"WARNING: {state_name} end without start at {entry.get('timestamp')}"
                )
                continue

            intervals.append({
                "type": state_name,
                "start": start_entry,
                "end": entry,
                "start_time": start_entry["_timestamp"],
                "end_time": entry["_timestamp"],
            })

            open_states[state_name] = None

    for state_name, start_entry in open_states.items():
        if start_entry is not None:
            warnings.append(
                f"WARNING: {state_name} still open since {start_entry.get('timestamp')}"
            )

    return intervals, anchors, warnings


def filter_points(points, start_time, end_time):
    return [
        point for point in points
        if start_time <= point["timestamp"] <= end_time
    ]


def xml_escape(value):
    return html.escape(str(value), quote=True)


def gpx_track(track_name, points):
    if not points:
        return ""

    lines = []
    lines.append("  <trk>")
    lines.append(f"    <name>{xml_escape(track_name)}</name>")
    lines.append("    <trkseg>")

    for point in points:
        lines.append(
            f'      <trkpt lat="{point["lat"]:.9f}" lon="{point["lon"]:.9f}">'
            f'<time>{xml_escape(point["time"])}</time>'
            f'<course>{point["course"]:.2f}</course>'
            f'<speed>{point["speed"]:.6f}</speed>'
            f'</trkpt>'
        )

    lines.append("    </trkseg>")
    lines.append("  </trk>")

    return "\n".join(lines)


def gpx_anchor_waypoint(entry, index):
    lat = entry.get("lat")
    lon = entry.get("lon")

    if lat is None or lon is None:
        return ""

    text = entry.get("text") or ""
    timestamp = entry.get("timestamp") or ""
    name = f"Anker {index}"

    desc_parts = [timestamp]

    if text:
        desc_parts.append(text)

    desc = " - ".join(desc_parts)

    return "\n".join([
        f'  <wpt lat="{float(lat):.9f}" lon="{float(lon):.9f}">',
        f"    <name>{xml_escape(name)}</name>",
        f"    <desc>{xml_escape(desc)}</desc>",
        "    <sym>Anchor</sym>",
        "  </wpt>",
    ])


def build_gpx(date_value, intervals, anchors, points):
    lines = []

    lines.append('<?xml version="1.0" encoding="UTF-8" standalone="no" ?>')
    lines.append('<gpx xmlns="http://www.topografix.com/GPX/1/1"')
    lines.append('     version="1.1"')
    lines.append('     creator="avnav-logbuch-plugin"')
    lines.append('     xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"')
    lines.append('     xsi:schemaLocation="http://www.topografix.com/GPX/1/1 http://www.topografix.com/GPX/1/1/gpx.xsd">')
    lines.append(f"  <metadata><name>Logbook additional {xml_escape(date_value)}</name></metadata>")

    anchor_index = 1
    for anchor in anchors:
        wpt = gpx_anchor_waypoint(anchor, anchor_index)
        if wpt:
            lines.append(wpt)
            anchor_index += 1

    segment_counter = {
        "motor": 0,
        "sail": 0,
    }

    for interval in intervals:
        interval_type = interval["type"]

        if interval_type not in ("motor", "sail"):
            continue

        segment_points = filter_points(
            points,
            interval["start_time"],
            interval["end_time"],
        )

        if not segment_points:
            continue

        segment_counter[interval_type] += 1

        track_name = (
            f"{DISPLAY_NAMES[interval_type]} "
            f"{segment_counter[interval_type]} "
            f"{interval['start'].get('timestamp')} - {interval['end'].get('timestamp')}"
        )

        lines.append(gpx_track(track_name, segment_points))

    lines.append("</gpx>")
    lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Export AVNav logbuch additional GPX")
    parser.add_argument("--date", required=True, help="Date in YYYY-MM-DD format")
    parser.add_argument("--avnav-data", default="/home/pi/avnav/data", help="AVNav data directory")
    parser.add_argument("--output", default="", help="Optional output GPX file")
    parser.add_argument("--dry-run", action="store_true", help="Do not write output file")

    args = parser.parse_args()

    avnav_data = Path(args.avnav_data)
    tracks_dir = avnav_data / "tracks"
    logbuch_dir = avnav_data / "logbuch"

    avt_file = tracks_dir / f"{args.date}.avt"
    logbuch_file = logbuch_dir / f"logbuch-{args.date}.jsonl"

    if args.output:
        output_file = Path(args.output)
    else:
        output_file = tracks_dir / f"{args.date}_additional.gpx"

    entries = read_logbuch(logbuch_file)
    points = read_avt(avt_file)

    intervals, anchors, warnings = build_intervals(entries)
    gpx = build_gpx(args.date, intervals, anchors, points)

    print(f"Logbuch entries: {len(entries)}")
    print(f"Track points: {len(points)}")
    print(f"Intervals: {len(intervals)}")
    print(f"Anchor points: {len(anchors)}")
    print(f"Output: {output_file}")

    for warning in warnings:
        print(warning)

    if not args.dry_run:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(gpx, encoding="utf-8")
        print("GPX written.")


if __name__ == "__main__":
    main()
