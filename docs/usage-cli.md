# CLI Nutzung

Zentrales Menü:

```bash
python3 tools/logbook_manager.py
Funktionen
KMZ für ein bestimmtes Datum erzeugen
KMZ für heute erzeugen
Testdaten erzeugen
Testdaten exportieren und prüfen
Logbuchdateien anzeigen
Trackdateien anzeigen
KMZ-Inhalt prüfen
Live-Installation / Update-Hinweise anzeigen
Beenden
Direkter KMZ Export
python3 tools/export_additional_kmz.py --date 2026-05-24 --avnav-data /home/pi/avnav/data

Ausgabe:

/home/pi/avnav/data/tracks/YYYYMMDD_logbuch.kmz

Vorhandene KMZ-Dateien werden überschrieben.

Testdaten
python3 tools/logbook_manager.py

Dann Option:

4

Erwartete Testwerte:

Motorzeit: 00:20:00
Segelzeit: 00:15:00
Motor-Koordinaten: 5
Segel-Koordinaten: 4
Ankerpunkte: 1
Logbuchnotizen: 1


## Törn-KMZ Export

Direkt:

```bash
python3 tools/export_trip_kmz.py \
  --from-date 2026-05-21 \
  --to-date 2026-05-24 \
  --avnav-data /home/pi/avnav/data

Über Menü:

python3 tools/logbook_manager.py

Dann Option:

3


## Törn-KMZ Export

Direkt:

```bash
python3 tools/export_trip_kmz.py \
  --from-date 2026-05-21 \
  --to-date 2026-05-24 \
  --avnav-data /home/pi/avnav/data

Über Menü:

python3 tools/logbook_manager.py

Dann Option:

3


## Törn-KMZ Export

Direkt:

```bash
python3 tools/export_trip_kmz.py \
  --from-date 2026-05-21 \
  --to-date 2026-05-24 \
  --avnav-data /home/pi/avnav/data

Über Menü:

python3 tools/logbook_manager.py

Dann Option:

3


## Törn-KMZ Export

Direkt:


## Törn-KMZ Export

Direkt:


Automatische Pfaderkennung

Alle Tools verwenden die zentrale Pfaderkennung aus:

tools/common.py

Reihenfolge:

1. --avnav-data
2. AVNAV_DATA_DIR
3. /home/pi/avnav/data
4. /var/lib/avnav

Beispiel ohne expliziten Pfad:

python3 tools/export_additional_kmz.py --date 2026-05-24

Beispiel mit Umgebungsvariable:

export AVNAV_DATA_DIR=/var/lib/avnav
python3 tools/export_trip_kmz.py --from-date 2026-05-21 --to-date 2026-05-24


WebUI/API Export

Asynchroner Tagesexport:

curl "http://localhost:8080/plugins/user-logbuch/api/exportKmz?date=2026-05-24"

Asynchroner Törnexport:

curl "http://localhost:8080/plugins/user-logbuch/api/exportTripKmz?from=2026-05-21&to=2026-05-24"

Jobstatus:

curl "http://localhost:8080/plugins/user-logbuch/api/exportStatus"


Overlay Export Buttons

Im Logbuch-Overlay gibt es kleine Utility-Buttons:

KMZ Heute
Törn 7 Tage

Die Exporte laufen asynchron über die Plugin-API und schreiben nach:

AVNAV_DATA_DIR/overlays/


Overlay Export Buttons

Im Logbuch-Overlay gibt es kleine Utility-Buttons:

KMZ Heute
Törn 7 Tage

Die Exporte laufen asynchron über die Plugin-API und schreiben nach:

AVNAV_DATA_DIR/overlays/


Törn Start / Törn Ende im Overlay

Im Logbuch-Overlay gibt es kleine Buttons:

Törn Start
Törn Ende

Sie speichern die Events:

trip_start
trip_end

Diese Marker werden in KMZ-Exporten berücksichtigt.

Törn Start / Törn Ende im Overlay

Im Logbuch-Overlay gibt es kleine Buttons:

Törn Start
Törn Ende

Sie speichern die Events:

trip_start
trip_end

Diese Marker werden in KMZ-Exporten berücksichtigt.

Törn Export im Overlay

Der Button:

Törn Export

fragt nach:

1 = letzte 7 Tage
2 = seit letztem Törn Start

Für seit letztem Törn Start wird der letzte trip_start gesucht. Falls danach ein trip_end existiert, endet der Export dort. Andernfalls endet er heute.
