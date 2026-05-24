#!/usr/bin/env python3
"""
Export additional KMZ overlay for AVNav / Google Earth.

Creates one daily KMZ file:

    YYYYMMDD_logbuch.kmz

Input:
- AVNav GPX track file:
    tracks/YYYY-MM-DD.gpx

- Logbook JSONL file, preferred:
    logbook/YYYYMMDD_logbuch.jsonl

- Legacy fallback:
    logbook/logbook-YYYY-MM-DD.jsonl

If no --date is supplied, the script asks interactively.

Existing KMZ output is overwritten without asking.
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


def normalize_date(value):
    """Accept YYYY-MM-DD or YYYYMMDD and return both formats."""
    value = (value or "").strip()

    if not value:
        today = datetime.utcnow()
        return today.strftime("%Y-%m-%d"), today.strftime("%Y%m%d")

    if len(value) == 8 and value.isdigit():
        dt = datetime.strptime(value, "%Y%m%d")
        return dt.strftime("%Y-%m-%d"), dt.strftime("%Y%m%d")

    dt = datetime.strptime(value, "%Y-%m-%d")
    return dt.strftime("%Y-%m-%d"), dt.strftime("%Y%m%d")


def parse_time(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def escape(value):
    return html.escape(str(value), quote=True)


def find_logbook_file(logbook_dir, date_dash, date_compact):
    preferred = logbook_dir / f"{date_compact}_logbuch.jsonl"
    legacy = logbook_dir / f"logbook-{date_dash}.jsonl"

    if preferred.exists():
        return preferred

    if legacy.exists():
        return legacy

    raise FileNotFoundError(
        "No logbook file found. Tried:\n"
        f"  {preferred}\n"
        f"  {legacy}"
    )


def read_logbook(path):
    entries = []

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

        points.append({
            "timestamp": timestamp,
            "time": time_node.text,
            "lat": float(lat),
            "lon": float(lon),
            "course": float(course_node.text) if course_node is not None and course_node.text else None,
            "speed": float(speed_node.text) if speed_node is not None and speed_node.text else None,
        })

    points.sort(key=lambda item: item["timestamp"])
    return points


def build_intervals(entries):
    open_states = {
        "motor": None,
        "sail": None,
        "anchor": None,
    }

    # Merkt sich den ersten Eintrag des Tages, bei dem laut gespeichertem
    # state-Feld ein Zustand bereits aktiv war.
    #
    # Beispiel:
    # Das Boot lag zu Tagesbeginn bereits vor Anker.
    # Dann kann im Tagesfile zuerst "anchor_up" kommen, ohne dass vorher
    # "anchor_down" im gleichen Tagesfile steht.
    # In diesem Fall erzeugen wir einen synthetischen Startpunkt.
    first_active_state_entry = {
        "motor": None,
        "sail": None,
        "anchor": None,
    }

    intervals = []
    anchors = []
    notes = []
    warnings = []

    for entry in entries:
        state = entry.get("state") or {}

        for state_name in first_active_state_entry:
            if first_active_state_entry[state_name] is None and state.get(state_name) is True:
                first_active_state_entry[state_name] = entry

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
                synthetic_start = first_active_state_entry.get(state_name)

                if synthetic_start is not None and synthetic_start["_timestamp"] <= entry["_timestamp"]:
                    warnings.append(
                        f"INFO: {state_name} start inferred from saved state at "
                        f"{synthetic_start.get('timestamp')}"
                    )

                    start_entry = synthetic_start
                else:
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
    return [point for point in points if start_time <= point["timestamp"] <= end_time]


def kml_coordinates(points):
    return "\n".join(f'{point["lon"]:.9f},{point["lat"]:.9f},0' for point in points)


def kml_placemark_line(name, description, style_id, points):
    if not points:
        return ""

    return f"""
    <Placemark>
      <name>{escape(name)}</name>
      <description><![CDATA[{description}]]></description>
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
      <description><![CDATA[{description}]]></description>
      <styleUrl>#{style_id}</styleUrl>
      <Point>
        <coordinates>{float(lon):.9f},{float(lat):.9f},0</coordinates>
      </Point>
    </Placemark>
"""


def build_kml(date_dash, intervals, anchors, notes, points):
    motor_lines = []
    sail_lines = []
    anchor_points = []
    note_points = []

    motor_index = 1
    sail_index = 1

    for interval in intervals:
        interval_type = interval["type"]

        if interval_type not in ("motor", "sail"):
            continue

        segment_points = filter_points(points, interval["start_time"], interval["end_time"])

        if not segment_points:
            continue

        if interval_type == "motor":
            name = f"Motor {motor_index}"
            style = "motorLine"
            motor_index += 1
        else:
            name = f"Segel {sail_index}"
            style = "sailLine"
            sail_index += 1

        description = (
            f"<h2>{escape(name)}</h2>"
            f"<p><b>Start:</b> {escape(interval['start'].get('timestamp'))}<br>"
            f"<b>Ende:</b> {escape(interval['end'].get('timestamp'))}</p>"
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

        description = (
            f"<h2>Anker {index}</h2>"
            f"<p><b>Zeit:</b> {escape(timestamp)}</p>"
        )

        if text:
            description += f"<p>{escape(text)}</p>"

        anchor_points.append(kml_placemark_point(f"Anker {index}", description, "anchorPoint", lat, lon))

    for index, note in enumerate(notes, start=1):
        lat = note.get("lat")
        lon = note.get("lon")

        if lat is None or lon is None:
            continue

        text = note.get("text") or ""
        timestamp = note.get("timestamp") or ""

        description = (
            f"<h2>Logbuchnotiz {index}</h2>"
            f"<p><b>Zeit:</b> {escape(timestamp)}</p>"
        )

        if text:
            description += f"<p>{escape(text)}</p>"

        note_points.append(kml_placemark_point(f"Logbuchnotiz {index}", description, "notePoint", lat, lon))

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
<Document>
  <name>Logbuch {escape(date_dash)}</name>

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
        <href>icons/anchor.png</href>
      </Icon>
    </IconStyle>
  </Style>

  <Style id="notePoint">
    <IconStyle>
      <color>ffffffff</color>
      <scale>1.0</scale>
      <Icon>
        <href>icons/note.png</href>
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

    icons_dir = Path(__file__).parent / "kmz-icons"

    # mode="w" überschreibt vorhandene KMZ-Dateien ohne Rückfrage.
    with zipfile.ZipFile(output_file, "w", zipfile.ZIP_DEFLATED) as kmz:
        kmz.writestr("doc.kml", kml_content)

        anchor_icon = icons_dir / "anchor.png"
        note_icon = icons_dir / "note.png"

        if anchor_icon.exists():
            kmz.write(anchor_icon, "icons/anchor.png")

        if note_icon.exists():
            kmz.write(note_icon, "icons/note.png")


def main():
    parser = argparse.ArgumentParser(description="Export AVNav logbook KMZ")
    parser.add_argument("--date", default="", help="Date as YYYY-MM-DD or YYYYMMDD")
    parser.add_argument("--avnav-data", default="/home/pi/avnav/data", help="AVNav data directory")
    parser.add_argument("--output", default="", help="Optional output KMZ file")
    parser.add_argument("--dry-run", action="store_true", help="Do not write output file")

    args = parser.parse_args()

    if args.date:
        date_dash, date_compact = normalize_date(args.date)
    else:
        user_input = input("Welcher Tag soll erzeugt werden? [YYYY-MM-DD oder YYYYMMDD, leer=heute]: ")
        date_dash, date_compact = normalize_date(user_input)

    avnav_data = Path(args.avnav_data)
    tracks_dir = avnav_data / "tracks"
    logbook_dir = avnav_data / "logbook"

    gpx_file = tracks_dir / f"{date_dash}.gpx"
    logbook_file = find_logbook_file(logbook_dir, date_dash, date_compact)

    if args.output:
        output_file = Path(args.output)
    else:
        output_file = tracks_dir / f"{date_compact}_logbuch.kmz"

    entries = read_logbook(logbook_file)
    points = read_gpx_points(gpx_file)

    intervals, anchors, notes, warnings = build_intervals(entries)
    kml = build_kml(date_dash, intervals, anchors, notes, points)

    print(f"Date: {date_dash}")
    print(f"Logbook file: {logbook_file}")
    print(f"GPX file: {gpx_file}")
    print(f"Output: {output_file}")
    print(f"Logbook entries: {len(entries)}")
    print(f"Track points: {len(points)}")
    print(f"Intervals: {len(intervals)}")
    print(f"Anchor points: {len(anchors)}")
    print(f"Manual notes with position: {len(notes)}")

    for warning in warnings:
        print(warning)

    if not args.dry_run:
        write_kmz(output_file, kml)
        print("KMZ written. Existing file was overwritten if present.")


if __name__ == "__main__":
    main()
