#!/usr/bin/env python3
"""
Export additional KMZ overlay for AVNav / Google Earth.

Creates one daily KMZ file:

    YYYY-MM-DD_additional.kmz

The KMZ contains:
- motor segments as red KML lines
- sail segments as green KML lines
- anchor_down events as anchor placemarks
- manual logbook notes as note placemarks

Input:
- AVNav GPX track file: tracks/YYYY-MM-DD.gpx
- Logbook JSONL file:   logbook/logbook-YYYY-MM-DD.jsonl

Example:

    python3 tools/export_additional_kmz.py --date 2026-05-21 --avnav-data /home/pi/avnav/data
"""

import argparse
import html
import json
import zipfile
from datetime import datetime
from pathlib import Path
from xml.etree import ElementTree as ET


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


def parse_time(value):
    if not value:
        return None

    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def escape(value):
    return html.escape(str(value), quote=True)


def read_logbook(path):
    entries = []

    if not path.exists():
        raise FileNotFoundError(f"Logbook file not found: {path}")

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


def read_gpx_points(path):
    points = []

    if not path.exists():
        raise FileNotFoundError(f"GPX file not found: {path}")

    ET.register_namespace("", "http://www.topografix.com/GPX/1/1")
    tree = ET.parse(path)
    root = tree.getroot()

    namespace = {"gpx": "http://www.topografix.com/GPX/1/1"}

    for trkpt in root.findall(".//gpx:trkpt", namespace):
        lat = trkpt.attrib.get("lat")
        lon = trkpt.attrib.get("lon")
        time_node = trkpt.find("gpx:time", namespace)
        course_node = trkpt.find("gpx:course", namespace)
        speed_node = trkpt.find("gpx:speed", namespace)

        if lat is None or lon is None or time_node is None or not time_node.text:
            continue

        timestamp = parse_time(time_node.text)

        if timestamp is None:
            continue

        point = {
            "timestamp": timestamp,
            "time": time_node.text,
            "lat": float(lat),
            "lon": float(lon),
            "course": float(course_node.text) if course_node is not None and course_node.text else None,
            "speed": float(speed_node.text) if speed_node is not None and speed_node.text else None,
        }

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
    notes = []
    warnings = []

    for entry in entries:
        event_type = entry.get("event_type")

        if event_type == "manual":
            if entry.get("lat") is not None and entry.get("lon") is not None:
                notes.append(entry)
            continue

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

    return intervals, anchors, notes, warnings


def filter_points(points, start_time, end_time):
    return [
        point for point in points
        if start_time <= point["timestamp"] <= end_time
    ]


def kml_coordinates(points):
    lines = []

    for point in points:
        lines.append(f'{point["lon"]:.9f},{point["lat"]:.9f},0')

    return "\n".join(lines)


def kml_placemark_line(name, description, style_id, points):
    if not points:
        return ""

    return f"""
    <Placemark>
      <name>{escape(name)}</name>
      <description>{escape(description)}</description>
      <styleUrl>#{style_id}</styleUrl>
      <LineString>
        <tessellate>1</tessellate>
        <coordinates>
{kml_coordinates(points)}
        </coordinates>
      </LineString>
    </Placemark>
"""


def kml_placemark_point(name, description, style_id, lat, lon):
    return f"""
    <Placemark>
      <name>{escape(name)}</name>
      <description>{escape(description)}</description>
      <styleUrl>#{style_id}</styleUrl>
      <Point>
        <coordinates>{float(lon):.9f},{float(lat):.9f},0</coordinates>
      </Point>
    </Placemark>
"""


def build_kml(date_value, intervals, anchors, notes, points):
    motor_index = 1
    sail_index = 1

    motor_lines = []
    sail_lines = []
    anchor_points = []
    note_points = []

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

        if interval_type == "motor":
            name = f"Motor {motor_index}"
            motor_index += 1
            style = "motorLine"
        else:
            name = f"Segel {sail_index}"
            sail_index += 1
            style = "sailLine"

        description = (
            f"Start: {interval['start'].get('timestamp')}\\n"
            f"Ende: {interval['end'].get('timestamp')}"
        )

        line = kml_placemark_line(name, description, style, segment_points)

        if interval_type == "motor":
            motor_lines.append(line)
        else:
            sail_lines.append(line)

    for index, anchor in enumerate(anchors, start=1):
        lat = anchor.get("lat")
        lon = anchor.get("lon")

        if lat is None or lon is None:
            continue

        text = anchor.get("text") or ""
        timestamp = anchor.get("timestamp") or ""

        description = timestamp
        if text:
            description += "\\n" + text

        anchor_points.append(
            kml_placemark_point(
                f"Anker {index}",
                description,
                "anchorPoint",
                lat,
                lon,
            )
        )

    for index, note in enumerate(notes, start=1):
        lat = note.get("lat")
        lon = note.get("lon")

        if lat is None or lon is None:
            continue

        text = note.get("text") or ""
        timestamp = note.get("timestamp") or ""

        description = timestamp
        if text:
            description += "\\n" + text

        note_points.append(
            kml_placemark_point(
                f"Logbuchnotiz {index}",
                description,
                "notePoint",
                lat,
                lon,
            )
        )

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
<Document>
  <name>Logbook additional {escape(date_value)}</name>

  <Style id="motorLine">
    <LineStyle>
      <color>ff0000ff</color>
      <width>4</width>
    </LineStyle>
  </Style>

  <Style id="sailLine">
    <LineStyle>
      <color>ff00aa00</color>
      <width>4</width>
    </LineStyle>
  </Style>

  <Style id="anchorPoint">
    <IconStyle>
      <color>ff00aaff</color>
      <scale>1.2</scale>
      <Icon>
        <href>http://maps.google.com/mapfiles/kml/shapes/anchor.png</href>
      </Icon>
    </IconStyle>
  </Style>

  <Style id="notePoint">
    <IconStyle>
      <color>ffffffff</color>
      <scale>1.0</scale>
      <Icon>
        <href>http://maps.google.com/mapfiles/kml/shapes/info-i.png</href>
      </Icon>
    </IconStyle>
  </Style>

  <Folder>
    <name>Motorstrecken</name>
{''.join(motor_lines)}
  </Folder>

  <Folder>
    <name>Segelstrecken</name>
{''.join(sail_lines)}
  </Folder>

  <Folder>
    <name>Ankerpunkte</name>
{''.join(anchor_points)}
  </Folder>

  <Folder>
    <name>Logbuchnotizen</name>
{''.join(note_points)}
  </Folder>

</Document>
</kml>
"""


def write_kmz(output_file, kml_content):
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(output_file, "w", zipfile.ZIP_DEFLATED) as kmz:
        kmz.writestr("doc.kml", kml_content)


def main():
    parser = argparse.ArgumentParser(description="Export AVNav logbook additional KMZ")
    parser.add_argument("--date", required=True, help="Date in YYYY-MM-DD format")
    parser.add_argument("--avnav-data", default="/home/pi/avnav/data", help="AVNav data directory")
    parser.add_argument("--output", default="", help="Optional output KMZ file")
    parser.add_argument("--dry-run", action="store_true", help="Do not write output file")

    args = parser.parse_args()

    avnav_data = Path(args.avnav_data)
    tracks_dir = avnav_data / "tracks"
    logbook_dir = avnav_data / "logbook"

    gpx_file = tracks_dir / f"{args.date}.gpx"
    logbook_file = logbook_dir / f"logbook-{args.date}.jsonl"

    if args.output:
        output_file = Path(args.output)
    else:
        output_file = tracks_dir / f"{args.date}_additional.kmz"

    entries = read_logbook(logbook_file)
    points = read_gpx_points(gpx_file)

    intervals, anchors, notes, warnings = build_intervals(entries)
    kml = build_kml(args.date, intervals, anchors, notes, points)

    print(f"Logbook entries: {len(entries)}")
    print(f"Track points: {len(points)}")
    print(f"Intervals: {len(intervals)}")
    print(f"Anchor points: {len(anchors)}")
    print(f"Manual notes with position: {len(notes)}")
    print(f"Output: {output_file}")

    for warning in warnings:
        print(warning)

    if not args.dry_run:
        write_kmz(output_file, kml)
        print("KMZ written.")


if __name__ == "__main__":
    main()
