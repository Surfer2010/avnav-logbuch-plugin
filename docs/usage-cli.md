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

