#!/usr/bin/env python3
"""
AVNav Logbuch Manager

Zentrales CLI-Menü für wiederkehrende Aufgaben:

1. KMZ für bestimmtes Datum erzeugen
2. KMZ für heute erzeugen
3. Testdaten erzeugen
4. Testdaten auswerten
5. Logbuchdateien anzeigen
6. Trackdateien anzeigen
7. KMZ-Inhalt prüfen
8. Hinweise zur Live-Installation anzeigen
9. Beenden
"""

import os
import subprocess
from datetime import datetime
from pathlib import Path

from common import detect_avnav_data_dir, get_logbook_dir, get_tracks_dir, print_detected_paths


PROJECT_ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = PROJECT_ROOT / "tools"

TEST_AVNAV_DATA = PROJECT_ROOT / "testdata" / "avnav-data"


def run(command):
    """
    Shell-Befehl ausführen und direkt anzeigen.
    """

    print()
    print("Befehl:")
    print(" ".join(str(part) for part in command))
    print()

    subprocess.run(command, check=False)


def ask_avnav_data():
    """
    AVNav-Datenverzeichnis abfragen.

    Leer bedeutet:
    automatische Erkennung über common.py
    """

    detected = detect_avnav_data_dir()
    print_detected_paths(detected)

    value = input(f"AVNav data directory [{detected}]: ").strip()

    if not value:
        return str(detected)

    return value


def ask_date(default_today=True):
    """
    Datum abfragen.

    Akzeptiert:
    - YYYY-MM-DD
    - YYYYMMDD
    """

    today = datetime.utcnow().strftime("%Y-%m-%d")

    if default_today:
        value = input(f"Datum [{today}]: ").strip()
        return value or today

    return input("Datum [YYYY-MM-DD oder YYYYMMDD]: ").strip()


def export_kmz_for_date():
    """
    KMZ für frei wählbares Datum erzeugen.
    """

    date_value = ask_date(default_today=False)
    avnav_data = ask_avnav_data()

    run([
        "python3",
        str(TOOLS_DIR / "export_additional_kmz.py"),
        "--date",
        date_value,
        "--avnav-data",
        avnav_data,
    ])


def export_kmz_today():
    """
    KMZ für heutigen Tag erzeugen.
    """

    date_value = datetime.utcnow().strftime("%Y-%m-%d")
    avnav_data = ask_avnav_data()

    run([
        "python3",
        str(TOOLS_DIR / "export_additional_kmz.py"),
        "--date",
        date_value,
        "--avnav-data",
        avnav_data,
    ])



def export_trip_kmz():
    """
    Multi-Day / Törn-KMZ erzeugen.
    """

    from_date = input("Startdatum [YYYY-MM-DD oder YYYYMMDD]: ").strip()
    to_date = input("Enddatum [YYYY-MM-DD oder YYYYMMDD]: ").strip()
    avnav_data = ask_avnav_data()

    run([
        "python3",
        str(TOOLS_DIR / "export_trip_kmz.py"),
        "--from-date",
        from_date,
        "--to-date",
        to_date,
        "--avnav-data",
        avnav_data,
    ])


def create_testdata():
    """
    Reproduzierbare Testdaten erzeugen.

    Enthält:
    - einen GPX-Track
    - ein Logbuch mit Motor, Segel, Anker, Notiz
    """

    logbook_dir = TEST_AVNAV_DATA / "logbook"
    tracks_dir = TEST_AVNAV_DATA / "tracks"

    logbook_dir.mkdir(parents=True, exist_ok=True)
    tracks_dir.mkdir(parents=True, exist_ok=True)

    gpx_file = tracks_dir / "2026-06-01.gpx"
    logbook_file = logbook_dir / "20260601_logbuch.jsonl"

    gpx_file.write_text("""<?xml version="1.0" encoding="UTF-8" standalone="no" ?>
<gpx xmlns="http://www.topografix.com/GPX/1/1" version="1.1" creator="avnav-test">
  <trk>
    <name>avnav-track-2026-06-01</name>
    <trkseg>
      <trkpt lat="54.000000000" lon="10.000000000"><time>2026-06-01T10:00:00Z</time><course>90.0</course><speed>2.0</speed></trkpt>
      <trkpt lat="54.000000000" lon="10.010000000"><time>2026-06-01T10:05:00Z</time><course>90.0</course><speed>2.2</speed></trkpt>
      <trkpt lat="54.000000000" lon="10.020000000"><time>2026-06-01T10:10:00Z</time><course>90.0</course><speed>2.4</speed></trkpt>
      <trkpt lat="54.000000000" lon="10.030000000"><time>2026-06-01T10:15:00Z</time><course>90.0</course><speed>2.6</speed></trkpt>
      <trkpt lat="54.000000000" lon="10.040000000"><time>2026-06-01T10:20:00Z</time><course>90.0</course><speed>2.8</speed></trkpt>
      <trkpt lat="54.010000000" lon="10.050000000"><time>2026-06-01T10:25:00Z</time><course>45.0</course><speed>4.0</speed></trkpt>
      <trkpt lat="54.020000000" lon="10.060000000"><time>2026-06-01T10:30:00Z</time><course>45.0</course><speed>4.2</speed></trkpt>
      <trkpt lat="54.030000000" lon="10.070000000"><time>2026-06-01T10:35:00Z</time><course>45.0</course><speed>4.4</speed></trkpt>
      <trkpt lat="54.040000000" lon="10.080000000"><time>2026-06-01T10:40:00Z</time><course>45.0</course><speed>4.6</speed></trkpt>
      <trkpt lat="54.050000000" lon="10.090000000"><time>2026-06-01T10:45:00Z</time><course>10.0</course><speed>0.0</speed></trkpt>
      <trkpt lat="54.050100000" lon="10.090100000"><time>2026-06-01T10:50:00Z</time><course>10.0</course><speed>0.0</speed></trkpt>
    </trkseg>
  </trk>
</gpx>
""", encoding="utf-8")

    logbook_file.write_text("""{"timestamp":"2026-06-01T10:00:00Z","event_type":"motor_on","text":"","lat":54.000000,"lon":10.000000,"state":{"motor":true,"sail":false,"anchor":false},"source":"test"}
{"timestamp":"2026-06-01T10:20:00Z","event_type":"motor_off","text":"","lat":54.000000,"lon":10.040000,"state":{"motor":false,"sail":false,"anchor":false},"source":"test"}
{"timestamp":"2026-06-01T10:25:00Z","event_type":"sail_set","text":"","lat":54.010000,"lon":10.050000,"state":{"motor":false,"sail":true,"anchor":false},"source":"test"}
{"timestamp":"2026-06-01T10:40:00Z","event_type":"sail_down","text":"","lat":54.040000,"lon":10.080000,"state":{"motor":false,"sail":false,"anchor":false},"source":"test"}
{"timestamp":"2026-06-01T10:45:00Z","event_type":"anchor_down","text":"Testankerplatz","lat":54.050000,"lon":10.090000,"state":{"motor":false,"sail":false,"anchor":true},"source":"test"}
{"timestamp":"2026-06-01T10:50:00Z","event_type":"manual","text":"Testnotiz am Ankerplatz","lat":54.050100,"lon":10.090100,"state":{"motor":false,"sail":false,"anchor":true},"source":"test"}
""", encoding="utf-8")

    print()
    print("Testdaten erzeugt:")
    print(gpx_file)
    print(logbook_file)


def run_testdata_export():
    """
    Testdaten exportieren und zentrale Werte prüfen.
    """

    create_testdata()

    run([
        "python3",
        str(TOOLS_DIR / "export_additional_kmz.py"),
        "--date",
        "2026-06-01",
        "--avnav-data",
        str(TEST_AVNAV_DATA),
    ])

    kmz_file = TEST_AVNAV_DATA / "tracks" / "20260601_logbuch.kmz"

    print()
    print("KMZ Inhalt:")
    run(["unzip", "-l", str(kmz_file)])

    print()
    print("Erwartete Werte:")
    print("- Motorzeit: 00:20:00")
    print("- Segelzeit: 00:15:00")
    print("- Motor-Koordinaten: 5")
    print("- Segel-Koordinaten: 4")
    print("- Ankerpunkte: 1")
    print("- Logbuchnotizen: 1")

    print()
    print("KML Zusammenfassung:")
    run([
        "bash",
        "-c",
        f"unzip -p {kmz_file} doc.kml | grep -E 'Motorzeit|Segelzeit|Ankerpunkte|Logbuchnotizen|Motor 1|Segel 1|Anker 1|Logbuchnotiz'",
    ])


def list_logbook_files():
    """
    Logbuchdateien anzeigen.
    """

    avnav_data = ask_avnav_data()
    logbook_dir = get_logbook_dir(Path(avnav_data))

    run(["ls", "-lah", str(logbook_dir)])


def list_track_files():
    """
    Trackdateien anzeigen.
    """

    avnav_data = ask_avnav_data()
    tracks_dir = get_tracks_dir(Path(avnav_data))

    run(["ls", "-lah", str(tracks_dir)])


def inspect_kmz():
    """
    KMZ-Inhalt anzeigen.
    """

    path = input("Pfad zur KMZ-Datei: ").strip()

    if not path:
        print("Kein Pfad angegeben.")
        return

    run(["unzip", "-l", path])


def show_install_hints():
    """
    Hinweise für Live-Update anzeigen.
    """

    print()
    print("Live-Update Beispiel:")
    print()
    print("cd /tmp")
    print("wget https://raw.githubusercontent.com/Surfer2010/avnav-logbuch-plugin/test/additional-gpx-direct-widgets/tools/install_or_update.sh -O install_or_update.sh")
    print("chmod +x install_or_update.sh")
    print("./install_or_update.sh --branch test/additional-gpx-direct-widgets")
    print()
    print("KMZ-Exporter holen:")
    print()
    print("wget https://raw.githubusercontent.com/Surfer2010/avnav-logbuch-plugin/test/additional-gpx-direct-widgets/tools/export_additional_kmz.py -O export_additional_kmz.py")
    print("chmod +x export_additional_kmz.py")


def menu():
    """
    Hauptmenü.
    """

    while True:
        print()
        print("====================================")
        print("AVNav Logbuch Manager")
        print("====================================")
        print("1  KMZ für Datum erzeugen")
        print("2  KMZ für heute erzeugen")
        print("3  Törn-KMZ für Datumsbereich erzeugen")
        print("4  Testdaten erzeugen")
        print("5  Testdaten exportieren und prüfen")
        print("6  Logbuchdateien anzeigen")
        print("7  Trackdateien anzeigen")
        print("8  KMZ-Inhalt prüfen")
        print("9  Live-Installation / Update Hinweise")
        print("0  Beenden")
        print()

        choice = input("Auswahl: ").strip()

        if choice == "1":
            export_kmz_for_date()
        elif choice == "2":
            export_kmz_today()
        elif choice == "3":
            export_trip_kmz()
        elif choice == "4":
            create_testdata()
        elif choice == "5":
            run_testdata_export()
        elif choice == "6":
            list_logbook_files()
        elif choice == "7":
            list_track_files()
        elif choice == "8":
            inspect_kmz()
        elif choice == "9":
            show_install_hints()
        elif choice == "0":
            break
        else:
            print("Ungültige Auswahl.")


if __name__ == "__main__":
    menu()
