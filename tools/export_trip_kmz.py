#!/usr/bin/env python3
"""
AVNav Logbook Multi-Day / Törn KMZ Export

Erzeugt eine gemeinsame KMZ-Datei für mehrere Tage.

Input je Tag:
- tracks/YYYY-MM-DD.gpx
- logbook/YYYYMMDD_logbuch.jsonl
- fallback: logbook/logbook-YYYY-MM-DD.jsonl

Output:
- overlays/YYYYMMDD-YYYYMMDD_toern_logbuch.kmz

Die Datei enthält:
- Tagesordner
- Motorstrecken
- Segelstrecken
- Ankerpunkte
- Logbuchnotizen
- Tagesstatistiken je Tag
- Gesamtstatistik über den Zeitraum
- eingebettete Icons
"""

import argparse
import zipfile
from datetime import datetime, timedelta
from pathlib import Path

from common import detect_avnav_data_dir, get_logbook_dir, get_tracks_dir, get_overlays_dir, print_detected_paths

import export_additional_kmz as day_export


def daterange(start_date, end_date):
    """
    Erzeugt alle Tage zwischen Start und Ende inklusive.
    """

    current = start_date

    while current <= end_date:
        yield current
        current += timedelta(days=1)


def parse_date(value):
    """
    Akzeptiert:
    - YYYY-MM-DD
    - YYYYMMDD
    """

    value = value.strip()

    if len(value) == 8 and value.isdigit():
        return datetime.strptime(value, "%Y%m%d")

    return datetime.strptime(value, "%Y-%m-%d")


def add_stats(total, day_stats):
    """
    Tagesstatistik zur Gesamtstatistik addieren.
    """

    for key, value in day_stats.items():
        total[key] = total.get(key, 0) + value


def create_trip_description(start_dash, end_dash, stats):
    """
    Beschreibung für das gesamte Törn-Dokument.
    """

    return f"""
<![CDATA[

<h1>Törnlogbuch {day_export.escape(start_dash)} bis {day_export.escape(end_dash)}</h1>

<table border="1" cellpadding="4" cellspacing="0">

<tr>
<td><b>Motorzeit gesamt</b></td>
<td>{day_export.hms(stats.get("motor_seconds", 0))}</td>
</tr>

<tr>
<td><b>Segelzeit gesamt</b></td>
<td>{day_export.hms(stats.get("sail_seconds", 0))}</td>
</tr>

<tr>
<td><b>Ankerzeit gesamt</b></td>
<td>{day_export.hms(stats.get("anchor_seconds", 0))}</td>
</tr>

<tr>
<td><b>Motordistanz gesamt</b></td>
<td>{stats.get("motor_distance_nm", 0.0):.2f} sm</td>
</tr>

<tr>
<td><b>Segeldistanz gesamt</b></td>
<td>{stats.get("sail_distance_nm", 0.0):.2f} sm</td>
</tr>

<tr>
<td><b>Gesamtdistanz</b></td>
<td>{stats.get("total_distance_nm", 0.0):.2f} sm</td>
</tr>

<tr>
<td><b>Motorstrecken</b></td>
<td>{stats.get("motor_count", 0)}</td>
</tr>

<tr>
<td><b>Segelstrecken</b></td>
<td>{stats.get("sail_count", 0)}</td>
</tr>

<tr>
<td><b>Ankerpunkte</b></td>
<td>{stats.get("anchor_count", 0)}</td>
</tr>

<tr>
<td><b>Logbuchnotizen</b></td>
<td>{stats.get("note_count", 0)}</td>
</tr>

</table>

]]>
"""


def build_day_folder(date_dash, entries, track_points):
    """
    Erzeugt einen KML-Ordner für einen Tag.
    """

    intervals, anchors, notes, warnings = day_export.build_intervals(entries)
    motor_placemarks = []
    sail_placemarks = []
    anchor_placemarks = []
    note_placemarks = []

    motor_index = 1
    sail_index = 1

    for interval in intervals:
        points = day_export.collect_interval_points(interval, track_points)

        if not points:
            continue

        metrics = day_export.calculate_track_metrics(
            points,
            interval["duration_seconds"],
        )

        interval.update(metrics)
        interval["track_point_count"] = len(points)

        description = day_export.create_interval_description(interval)

        if interval["type"] == "motor":
            motor_placemarks.append(
                day_export.kml_line_placemark(
                    f"{date_dash} Motor {motor_index}",
                    description,
                    "motorLine",
                    points,
                    interval,
                )
            )
            motor_index += 1

        elif interval["type"] == "sail":
            sail_placemarks.append(
                day_export.kml_line_placemark(
                    f"{date_dash} Segel {sail_index}",
                    description,
                    "sailLine",
                    points,
                    interval,
                )
            )
            sail_index += 1

    for index, anchor in enumerate(anchors, start=1):
        if anchor.get("lat") is None or anchor.get("lon") is None:
            continue

        title = f"{date_dash} Anker {index}"

        anchor_placemarks.append(
            day_export.kml_point_placemark(
                title,
                day_export.create_point_description(title, anchor),
                "anchorPoint",
                anchor.get("lat"),
                anchor.get("lon"),
                anchor.get("timestamp"),
            )
        )

    for index, note in enumerate(notes, start=1):
        if note.get("lat") is None or note.get("lon") is None:
            continue

        title = f"{date_dash} Logbuchnotiz {index}"

        note_placemarks.append(
            day_export.kml_point_placemark(
                title,
                day_export.create_point_description(title, note),
                "notePoint",
                note.get("lat"),
                note.get("lon"),
                note.get("timestamp"),
            )
        )

    stats = day_export.build_daily_stats(intervals, anchors, notes)

    day_description = day_export.create_document_description(date_dash, stats)

    folder = f"""
  <Folder>
    <name>{day_export.escape(date_dash)}</name>
    <description>
{day_description}
    </description>

    <Folder>
      <name>Motorstrecken</name>
{''.join(motor_placemarks)}
    </Folder>

    <Folder>
      <name>Segelstrecken</name>
{''.join(sail_placemarks)}
    </Folder>

    <Folder>
      <name>Ankerpunkte</name>
{''.join(anchor_placemarks)}
    </Folder>

    <Folder>
      <name>Logbuchnotizen</name>
{''.join(note_placemarks)}
    </Folder>

  </Folder>
"""

    return folder, stats, warnings


def build_trip_kml(start_dash, end_dash, day_folders, total_stats):
    """
    Erzeugt das vollständige KML-Dokument für den Törn.
    """

    description = create_trip_description(start_dash, end_dash, total_stats)

    return f'''<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
<Document>

  <name>Törnlogbuch {day_export.escape(start_dash)} bis {day_export.escape(end_dash)}</name>
  <description>
{description}
  </description>

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
      <scale>1.2</scale>
      <Icon>
        <href>icons/anchor.png</href>
      </Icon>
    </IconStyle>
  </Style>

  <Style id="notePoint">
    <IconStyle>
      <scale>1.0</scale>
      <Icon>
        <href>icons/note.png</href>
      </Icon>
    </IconStyle>
  </Style>

{''.join(day_folders)}

</Document>
</kml>
'''


def write_trip_kmz(output_file, kml_content):
    """
    Schreibt KMZ inklusive lokaler Icons.
    """

    output_file.parent.mkdir(parents=True, exist_ok=True)

    icons_dir = Path(__file__).parent / "kmz-icons"

    with zipfile.ZipFile(output_file, "w", zipfile.ZIP_DEFLATED) as kmz:
        kmz.writestr("doc.kml", kml_content)

        anchor_icon = icons_dir / "anchor.png"
        note_icon = icons_dir / "note.png"

        if anchor_icon.exists():
            kmz.write(anchor_icon, "icons/anchor.png")

        if note_icon.exists():
            kmz.write(note_icon, "icons/note.png")


def main():
    parser = argparse.ArgumentParser(description="Export AVNav Törn KMZ")
    parser.add_argument("--from-date", required=True, help="Startdatum YYYY-MM-DD oder YYYYMMDD")
    parser.add_argument("--to-date", required=True, help="Enddatum YYYY-MM-DD oder YYYYMMDD")
    parser.add_argument("--avnav-data", default="", help="AVNav Datenverzeichnis. Leer = automatisch erkennen.")
    parser.add_argument("--output", default="", help="Optionaler KMZ-Ausgabepfad")
    parser.add_argument("--dry-run", action="store_true", help="Nicht schreiben, nur prüfen")

    args = parser.parse_args()

    start_date = parse_date(args.from_date)
    end_date = parse_date(args.to_date)

    if end_date < start_date:
        raise SystemExit("Enddatum liegt vor Startdatum.")

    avnav_data = detect_avnav_data_dir(args.avnav_data)
    tracks_dir = get_tracks_dir(avnav_data)
    overlays_dir = get_overlays_dir(avnav_data)
    logbook_dir = get_logbook_dir(avnav_data)

    start_dash = start_date.strftime("%Y-%m-%d")
    end_dash = end_date.strftime("%Y-%m-%d")
    start_compact = start_date.strftime("%Y%m%d")
    end_compact = end_date.strftime("%Y%m%d")

    print_detected_paths(avnav_data)

    if args.output:
        output_file = Path(args.output)
    else:
        output_file = overlays_dir / f"{start_compact}-{end_compact}_toern_logbuch.kmz"

    day_folders = []
    total_stats = {}
    all_warnings = []

    for day in daterange(start_date, end_date):
        date_dash = day.strftime("%Y-%m-%d")
        date_compact = day.strftime("%Y%m%d")

        gpx_file = tracks_dir / f"{date_dash}.gpx"

        try:
            logbook_file = day_export.find_logbook_file(
                logbook_dir,
                date_dash,
                date_compact,
            )
        except FileNotFoundError:
            print(f"SKIP: no logbook file for {date_dash}")
            continue

        if not gpx_file.exists():
            print(f"SKIP: no GPX file for {date_dash}: {gpx_file}")
            continue

        entries = day_export.read_logbook(logbook_file)
        track_points = day_export.read_gpx_points(gpx_file)

        folder, stats, warnings = build_day_folder(
            date_dash,
            entries,
            track_points,
        )

        add_stats(total_stats, stats)
        day_folders.append(folder)

        for warning in warnings:
            all_warnings.append(f"{date_dash}: {warning}")

        print(f"DAY: {date_dash}")
        print(f"  Logbook: {logbook_file}")
        print(f"  GPX: {gpx_file}")
        print(f"  Entries: {len(entries)}")
        print(f"  Track points: {len(track_points)}")

    kml_content = build_trip_kml(
        start_dash,
        end_dash,
        day_folders,
        total_stats,
    )

    print(f"Output: {output_file}")
    print(f"Days included: {len(day_folders)}")
    print(f"Motor time: {day_export.hms(total_stats.get('motor_seconds', 0))}")
    print(f"Sail time: {day_export.hms(total_stats.get('sail_seconds', 0))}")
    print(f"Anchor time: {day_export.hms(total_stats.get('anchor_seconds', 0))}")

    for warning in all_warnings:
        print(warning)

    if args.dry_run:
        print("Dry run. No KMZ written.")
        return

    write_trip_kmz(output_file, kml_content)
    print("Trip KMZ written. Existing file was overwritten if present.")


if __name__ == "__main__":
    main()
