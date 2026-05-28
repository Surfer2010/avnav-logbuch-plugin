#!/usr/bin/env python3
"""
AVNav Logbuch → KMZ Export

Erzeugt eine Google-Earth-/KML-kompatible KMZ-Datei
aus:

- AVNav GPX Tagestrack
- AVNav Logbuch JSONL

Funktionen:
- Motorstrecken
- Segelstrecken
- Ankerpunkte
- Logbuchnotizen
- Tagesstatistiken
- Dauerberechnung
- eingebettete Icons
- automatische Wiederherstellung offener Zustände

Ausgabe:
YYYYMMDD_logbuch.kmz
"""

import argparse
import html
import json
import math
import zipfile

from datetime import datetime
from pathlib import Path

from common import detect_avnav_data_dir, get_logbook_dir, get_tracks_dir, get_overlays_dir, print_detected_paths
from xml.etree import ElementTree as ET


# Mapping:
# Welches Event startet welchen Zustand?
START_EVENTS = {
    "motor_on": "motor",
    "sail_set": "sail",
    "anchor_down": "anchor",
}

# Mapping:
# Welches Event beendet welchen Zustand?
END_EVENTS = {
    "motor_off": "motor",
    "sail_down": "sail",
    "anchor_up": "anchor",
}

# Benutzerfreundliche Namen.
LABELS = {
    "motor": "Motor",
    "sail": "Segel",
    "anchor": "Anker",
}


def normalize_date(value):
    """
    Akzeptiert:
    - YYYY-MM-DD
    - YYYYMMDD

    und liefert beide Formate zurück.
    """

    value = (value or "").strip()

    if not value:
        dt = datetime.utcnow()

    elif len(value) == 8 and value.isdigit():
        dt = datetime.strptime(value, "%Y%m%d")

    else:
        dt = datetime.strptime(value, "%Y-%m-%d")

    return (
        dt.strftime("%Y-%m-%d"),
        dt.strftime("%Y%m%d"),
    )


def parse_time(value):
    """
    ISO8601 → datetime

    Beispiel:
    2026-05-24T07:45:58Z
    """

    if not value:
        return None

    return datetime.fromisoformat(
        value.replace("Z", "+00:00")
    )


def escape(value):
    """
    HTML Escaping für sichere KML-Ausgabe.
    """

    return html.escape(str(value), quote=True)


def hms(seconds):
    """
    Sekunden → HH:MM:SS
    """

    seconds = int(max(0, seconds))

    return (
        f"{seconds // 3600:02d}:"
        f"{(seconds % 3600) // 60:02d}:"
        f"{seconds % 60:02d}"
    )


#
# Abstand zweier GPS-Punkte berechnen.
#
# Nutzt die Haversine-Formel.
# Ergebnis: Meter.
#
def haversine_meters(lat1, lon1, lat2, lon2):

    earth_radius_m = 6371000.0

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)

    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2) ** 2
        + math.cos(phi1)
        * math.cos(phi2)
        * math.sin(delta_lambda / 2) ** 2
    )

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return earth_radius_m * c


#
# Distanz und Durchschnittsgeschwindigkeit
# für einen Trackabschnitt berechnen.
#
# Distanz:
#   Summe aller Einzelabstände
#
# Durchschnitt:
#   Distanz / Dauer
#
def calculate_track_metrics(points, duration_seconds):

    distance_m = 0.0

    for index in range(1, len(points)):

        previous = points[index - 1]
        current = points[index]

        distance_m += haversine_meters(
            previous["lat"],
            previous["lon"],
            current["lat"],
            current["lon"],
        )

    distance_nm = distance_m / 1852.0

    if duration_seconds > 0:
        average_speed_kn = distance_nm / (duration_seconds / 3600.0)
    else:
        average_speed_kn = 0.0

    return {
        "distance_m": distance_m,
        "distance_nm": distance_nm,
        "average_speed_kn": average_speed_kn,
    }


def find_logbook_file(logbook_dir, date_dash, date_compact):
    """
    Sucht bevorzugt:
        YYYYMMDD_logbuch.jsonl

    und unterstützt zusätzlich:
        logbook-YYYY-MM-DD.jsonl
    """

    preferred = (
        logbook_dir /
        f"{date_compact}_logbuch.jsonl"
    )

    legacy = (
        logbook_dir /
        f"logbook-{date_dash}.jsonl"
    )

    if preferred.exists():
        return preferred

    if legacy.exists():
        return legacy

    raise FileNotFoundError(
        f"No logbook file found:\n"
        f"  {preferred}\n"
        f"  {legacy}"
    )


def read_logbook(path):
    """
    Lädt JSONL-Logbuchdatei.

    Jede Zeile:
        ein JSON-Eintrag
    """

    entries = []

    with path.open("r", encoding="utf-8") as handle:

        for line_number, line in enumerate(handle, start=1):

            line = line.strip()

            if not line:
                continue

            try:
                entry = json.loads(line)

                entry["_timestamp"] = parse_time(
                    entry.get("timestamp")
                )

                entries.append(entry)

            except Exception as error:
                print(
                    f"WARNING: invalid logbook line "
                    f"{path}:{line_number}: {error}"
                )

    entries.sort(
        key=lambda item: item["_timestamp"]
    )

    return entries


def read_gpx_points(path):
    """
    Liest GPX Trackpunkte.

    Benötigt:
    - Zeit
    - Lat
    - Lon
    """

    if not path.exists():
        raise FileNotFoundError(
            f"GPX file not found: {path}"
        )

    points = []

    tree = ET.parse(path)
    root = tree.getroot()

    namespace = {
        "gpx": "http://www.topografix.com/GPX/1/1"
    }

    for trkpt in root.findall(".//gpx:trkpt", namespace):

        time_node = trkpt.find(
            "gpx:time",
            namespace
        )

        course_node = trkpt.find(
            "gpx:course",
            namespace
        )

        speed_node = trkpt.find(
            "gpx:speed",
            namespace
        )

        if time_node is None or not time_node.text:
            continue

        points.append({
            "timestamp": parse_time(time_node.text),
            "time": time_node.text,
            "lat": float(trkpt.attrib["lat"]),
            "lon": float(trkpt.attrib["lon"]),
            "course": (
                float(course_node.text)
                if course_node is not None
                and course_node.text
                else None
            ),
            "speed": (
                float(speed_node.text)
                if speed_node is not None
                and speed_node.text
                else None
            ),
        })

    points.sort(
        key=lambda item: item["timestamp"]
    )

    return points


def build_intervals(entries):
    """
    Erzeugt:
    - Motorintervalle
    - Segelintervalle
    - Ankerintervalle

    Unterstützt:
    Wiederherstellung offener Zustände
    aus gespeicherten state-Feldern.
    """

    # Aktuell offene Zustände.
    open_states = {
        "motor": None,
        "sail": None,
        "anchor": None,
    }

    # Falls Tagesfile mit bereits aktivem
    # Zustand startet:
    #
    # Beispiel:
    # anchor=true beim ersten Eintrag.
    #
    # Dann kann später anchor_up kommen,
    # obwohl anchor_down nicht im
    # Tagesfile enthalten ist.
    first_active_state_entry = {
        "motor": None,
        "sail": None,
        "anchor": None,
    }

    intervals = []
    anchors = []
    notes = []
    warnings = []

    #
    # Ersten gespeicherten Zustand merken.
    #
    for entry in entries:

        state = entry.get("state") or {}

        for state_name in first_active_state_entry:

            if (
                first_active_state_entry[state_name]
                is None
                and state.get(state_name) is True
            ):
                first_active_state_entry[state_name] = entry

    #
    # Hauptverarbeitung.
    #
    for entry in entries:

        event_type = entry.get("event_type")

        #
        # Freitextnotizen separat sammeln.
        #
        if event_type in ("manual", "trip_start", "trip_end"):

            if (
                entry.get("lat") is not None
                and entry.get("lon") is not None
            ):
                notes.append(entry)

            continue

        #
        # Start-Events.
        #
        if event_type in START_EVENTS:

            state_name = START_EVENTS[event_type]

            if state_name == "anchor":
                anchors.append(entry)

            if open_states[state_name] is not None:

                warnings.append(
                    f"WARNING: {state_name} already open at "
                    f"{entry.get('timestamp')}"
                )

            open_states[state_name] = entry

        #
        # Ende-Events.
        #
        elif event_type in END_EVENTS:

            state_name = END_EVENTS[event_type]

            start_entry = open_states[state_name]

            #
            # Kein Start vorhanden?
            #
            if start_entry is None:

                synthetic_start = (
                    first_active_state_entry.get(state_name)
                )

                #
                # Zustand aus state-Feld ableiten.
                #
                if (
                    synthetic_start is not None
                    and synthetic_start["_timestamp"]
                    <= entry["_timestamp"]
                ):

                    warnings.append(
                        f"INFO: {state_name} start inferred "
                        f"from saved state at "
                        f"{synthetic_start.get('timestamp')}"
                    )

                    start_entry = synthetic_start

                else:

                    warnings.append(
                        f"WARNING: {state_name} end without start "
                        f"at {entry.get('timestamp')}"
                    )

                    continue

            #
            # Dauer berechnen.
            #
            duration_seconds = (
                entry["_timestamp"]
                - start_entry["_timestamp"]
            ).total_seconds()

            intervals.append({
                "type": state_name,
                "start": start_entry,
                "end": entry,
                "start_time": start_entry["_timestamp"],
                "end_time": entry["_timestamp"],
                "duration_seconds": duration_seconds,
                "duration": hms(duration_seconds),
            })

            open_states[state_name] = None

    #
    # Noch offene Zustände melden.
    #
    for state_name, start_entry in open_states.items():

        if start_entry is not None:

            warnings.append(
                f"WARNING: {state_name} still open since "
                f"{start_entry.get('timestamp')}"
            )

    return (
        intervals,
        anchors,
        notes,
        warnings,
    )


#
# GPX-Punkte eines Intervalls sammeln.
#
# Beispiel:
#   motor_on → motor_off
#
# Ergebnis:
#   Liste aller Trackpunkte innerhalb
#   dieses Zeitfensters.
#
def collect_interval_points(interval, track_points):

    result = []

    start_time = interval["start_time"]
    end_time = interval["end_time"]

    for point in track_points:

        timestamp = point["timestamp"]

        #
        # Ungültige Punkte ignorieren.
        #
        if timestamp is None:
            continue

        #
        # Punkt liegt innerhalb
        # des Intervalls.
        #
        if start_time <= timestamp <= end_time:
            result.append(point)

    return result


#
# Tagesstatistik erzeugen.
#
# Verwendet für:
#   - KML Dokumentbeschreibung
#   - spätere Törnstatistiken
#   - Overlay-Auswertungen
#
def build_daily_stats(intervals, anchors, notes):

    stats = {
        "motor_seconds": 0,
        "sail_seconds": 0,
        "anchor_seconds": 0,
        "motor_count": 0,
        "sail_count": 0,
        "anchor_count": len(anchors),
        "note_count": len(notes),
        "motor_distance_nm": 0.0,
        "sail_distance_nm": 0.0,
    }

    for interval in intervals:

        state_type = interval["type"]
        duration = interval["duration_seconds"]
        distance_nm = interval.get("distance_nm", 0.0)

        if state_type == "motor":

            stats["motor_seconds"] += duration
            stats["motor_count"] += 1
            stats["motor_distance_nm"] += distance_nm

        elif state_type == "sail":

            stats["sail_seconds"] += duration
            stats["sail_count"] += 1
            stats["sail_distance_nm"] += distance_nm

        elif state_type == "anchor":

            stats["anchor_seconds"] += duration

    stats["total_distance_nm"] = (
        stats["motor_distance_nm"]
        + stats["sail_distance_nm"]
    )

    return stats


def create_document_description(date_dash, stats):

    return f"""
<![CDATA[

<h1>Logbuch {escape(date_dash)}</h1>

<table border="1" cellpadding="4" cellspacing="0">

<tr>
<td><b>Motorzeit</b></td>
<td>{hms(stats["motor_seconds"])}</td>
</tr>

<tr>
<td><b>Segelzeit</b></td>
<td>{hms(stats["sail_seconds"])}</td>
</tr>

<tr>
<td><b>Ankerzeit</b></td>
<td>{hms(stats["anchor_seconds"])}</td>
</tr>

<tr>
<td><b>Motordistanz</b></td>
<td>{stats["motor_distance_nm"]:.2f} sm</td>
</tr>

<tr>
<td><b>Segeldistanz</b></td>
<td>{stats["sail_distance_nm"]:.2f} sm</td>
</tr>

<tr>
<td><b>Gesamtdistanz</b></td>
<td>{stats["total_distance_nm"]:.2f} sm</td>
</tr>

<tr>
<td><b>Motorstrecken</b></td>
<td>{stats["motor_count"]}</td>
</tr>

<tr>
<td><b>Segelstrecken</b></td>
<td>{stats["sail_count"]}</td>
</tr>

<tr>
<td><b>Ankerpunkte</b></td>
<td>{stats["anchor_count"]}</td>
</tr>

<tr>
<td><b>Logbuchnotizen</b></td>
<td>{stats["note_count"]}</td>
</tr>

</table>

]]>
"""


def kml_coordinates(points):

    lines = []

    for point in points:

        lines.append(
            f'{point["lon"]:.9f},'
            f'{point["lat"]:.9f},0'
        )

    return "\n".join(lines)


#
# KML Placemark für eine Linie erzeugen.
#
# Wird genutzt für:
#   - Motorstrecken
#   - Segelstrecken
#
def kml_line_placemark(name, description, style_id, points, interval=None):

    if not points:
        return ""

    coordinates = kml_coordinates(points)

    timespan = ""

    if interval is not None:
        timespan = f"""
      <TimeSpan>
        <begin>{escape(interval["start"].get("timestamp"))}</begin>
        <end>{escape(interval["end"].get("timestamp"))}</end>
      </TimeSpan>"""

    return f"""
    <Placemark>
      <name>{escape(name)}</name>
      <description><![CDATA[
{description}
      ]]></description>
      <styleUrl>#{style_id}</styleUrl>{timespan}
      <LineString>
        <tessellate>1</tessellate>
        <coordinates>
{coordinates}
        </coordinates>
      </LineString>
    </Placemark>
"""


def kml_point_placemark(name, description, style_id, lat, lon, timestamp=None):

    timestamp_block = ""

    if timestamp:
        timestamp_block = f"""
      <TimeStamp>
        <when>{escape(timestamp)}</when>
      </TimeStamp>"""

    return f"""
    <Placemark>
      <name>{escape(name)}</name>
      <description><![CDATA[
{description}
      ]]></description>
      <styleUrl>#{style_id}</styleUrl>{timestamp_block}
      <Point>
        <coordinates>{float(lon):.9f},{float(lat):.9f},0</coordinates>
      </Point>
    </Placemark>
"""


def create_interval_description(interval):

    start = interval["start"]
    end = interval["end"]

    return f"""
<h2>{escape(LABELS.get(interval["type"], interval["type"]))}</h2>

<table border="1" cellpadding="4" cellspacing="0">
<tr>
<td><b>Start</b></td>
<td>{escape(start.get("timestamp"))}</td>
</tr>
<tr>
<td><b>Ende</b></td>
<td>{escape(end.get("timestamp"))}</td>
</tr>
<tr>
<td><b>Dauer</b></td>
<td>{escape(interval.get("duration"))}</td>
</tr>
<tr>
<td><b>Distanz</b></td>
<td>{interval.get("distance_nm", 0.0):.2f} sm</td>
</tr>
<tr>
<td><b>Durchschnitt</b></td>
<td>{interval.get("average_speed_kn", 0.0):.2f} kn</td>
</tr>
<tr>
<td><b>Trackpunkte</b></td>
<td>{interval.get("track_point_count", 0)}</td>
</tr>
<tr>
<td><b>Startposition</b></td>
<td>{escape(start.get("lat"))}, {escape(start.get("lon"))}</td>
</tr>
<tr>
<td><b>Endposition</b></td>
<td>{escape(end.get("lat"))}, {escape(end.get("lon"))}</td>
</tr>
</table>
"""


def create_point_description(title, entry):

    text = entry.get("text") or ""

    html_text = ""

    if text:
        html_text = f"<p>{escape(text)}</p>"

    return f"""
<h2>{escape(title)}</h2>

<table border="1" cellpadding="4" cellspacing="0">
<tr>
<td><b>Zeit</b></td>
<td>{escape(entry.get("timestamp"))}</td>
</tr>
<tr>
<td><b>Position</b></td>
<td>{escape(entry.get("lat"))}, {escape(entry.get("lon"))}</td>
</tr>
</table>

{html_text}
"""




#
# Vollständiges KML-Dokument erzeugen.
#
def build_kml(date_dash, intervals, anchors, notes, track_points):

    motor_placemarks = []
    sail_placemarks = []
    anchor_placemarks = []
    note_placemarks = []

    motor_index = 1
    sail_index = 1

    #
    # Motor- und Segelstrecken erzeugen.
    #
    for interval in intervals:

        points = collect_interval_points(interval, track_points)

        if not points:
            continue

        metrics = calculate_track_metrics(
            points,
            interval["duration_seconds"],
        )

        interval.update(metrics)
        interval["track_point_count"] = len(points)

        description = create_interval_description(interval)

        if interval["type"] == "motor":

            motor_placemarks.append(
                kml_line_placemark(
                    f"Motor {motor_index}",
                    description,
                    "motorLine",
                    points,
                    interval,
                )
            )

            motor_index += 1

        elif interval["type"] == "sail":

            sail_placemarks.append(
                kml_line_placemark(
                    f"Segel {sail_index}",
                    description,
                    "sailLine",
                    points,
                    interval,
                )
            )

            sail_index += 1

    #
    # Ankerpunkte erzeugen.
    #
    for index, anchor in enumerate(anchors, start=1):

        if anchor.get("lat") is None or anchor.get("lon") is None:
            continue

        title = f"Anker {index}"

        anchor_placemarks.append(
            kml_point_placemark(
                title,
                create_point_description(title, anchor),
                "anchorPoint",
                anchor.get("lat"),
                anchor.get("lon"),
                anchor.get("timestamp"),
            )
        )

    #
    # Freitextnotizen erzeugen.
    #
    for index, note in enumerate(notes, start=1):

        if note.get("lat") is None or note.get("lon") is None:
            continue

        event_type = note.get("event_type")

        if event_type == "trip_start":
            title = "Törn Start"
        elif event_type == "trip_end":
            title = "Törn Ende"
        else:
            title = f"Logbuchnotiz {index}"

        note_placemarks.append(
            kml_point_placemark(
                title,
                create_point_description(title, note),
                "notePoint",
                note.get("lat"),
                note.get("lon"),
                note.get("timestamp"),
            )
        )

    stats = build_daily_stats(intervals, anchors, notes)

    document_description = create_document_description(
        date_dash,
        stats,
    )

    return f'''<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
<Document>

  <name>Logbuch {escape(date_dash)}</name>
  <description>
{document_description}
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

</Document>
</kml>
'''


#
# KMZ-Datei schreiben.
#
# Eine KMZ ist eine ZIP-Datei mit:
#   - doc.kml
#   - optionalen Ressourcen
#
def write_kmz(output_file, kml_content):

    output_file = Path(output_file)

    output_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    tmp_file = output_file.with_name(output_file.name + ".tmp")

    if tmp_file.exists():
        tmp_file.unlink()

    icons_dir = Path(__file__).parent / "kmz-icons"

    try:
        with zipfile.ZipFile(
            tmp_file,
            "w",
            zipfile.ZIP_DEFLATED,
        ) as kmz:

            kmz.writestr("doc.kml", kml_content)

            anchor_icon = icons_dir / "anchor.png"
            note_icon = icons_dir / "note.png"

            if anchor_icon.exists():
                kmz.write(anchor_icon, "icons/anchor.png")

            if note_icon.exists():
                kmz.write(note_icon, "icons/note.png")

        tmp_file.replace(output_file)

    finally:
        if tmp_file.exists():
            tmp_file.unlink()


#
# Hauptfunktion.
#
def main():

    parser = argparse.ArgumentParser(
        description="Export AVNav Logbuch KMZ"
    )

    parser.add_argument(
        "--date",
        default="",
        help="Datum als YYYY-MM-DD oder YYYYMMDD",
    )

    parser.add_argument(
        "--avnav-data",
        default="",
        help="AVNav Datenverzeichnis. Leer = automatisch erkennen.",
    )

    parser.add_argument(
        "--output",
        default="",
        help="Optionaler KMZ-Ausgabepfad",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Nicht schreiben, nur prüfen",
    )

    args = parser.parse_args()

    if args.date:
        date_dash, date_compact = normalize_date(args.date)
    else:
        user_input = input(
            "Welcher Tag soll erzeugt werden? "
            "[YYYY-MM-DD oder YYYYMMDD, leer=heute]: "
        )

        date_dash, date_compact = normalize_date(user_input)

    avnav_data = detect_avnav_data_dir(args.avnav_data)
    tracks_dir = get_tracks_dir(avnav_data)
    overlays_dir = get_overlays_dir(avnav_data)
    logbook_dir = get_logbook_dir(avnav_data)

    gpx_file = tracks_dir / f"{date_dash}.gpx"

    logbook_file = find_logbook_file(
        logbook_dir,
        date_dash,
        date_compact,
    )

    if args.output:
        output_file = Path(args.output)
    else:
        output_file = (
            overlays_dir /
            f"{date_compact}_logbuch.kmz"
        )

    entries = read_logbook(logbook_file)
    track_points = read_gpx_points(gpx_file)

    intervals, anchors, notes, warnings = build_intervals(
        entries
    )

    kml_content = build_kml(
        date_dash,
        intervals,
        anchors,
        notes,
        track_points,
    )

    print_detected_paths(avnav_data)
    print(f"Date: {date_dash}")
    print(f"Logbook file: {logbook_file}")
    print(f"GPX file: {gpx_file}")
    print(f"Output: {output_file}")
    print(f"Logbook entries: {len(entries)}")
    print(f"Track points: {len(track_points)}")
    print(f"Intervals: {len(intervals)}")
    print(f"Anchor points: {len(anchors)}")
    print(f"Manual notes with position: {len(notes)}")

    for warning in warnings:
        print(warning)

    if args.dry_run:
        print("Dry run. No KMZ written.")
        return

    write_kmz(
        output_file,
        kml_content,
    )

    print(
        "KMZ written. Existing file was overwritten "
        "if present."
    )


if __name__ == "__main__":
    main()
