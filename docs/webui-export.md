# WebUI/API KMZ Export

Das Plugin stellt asynchrone Export-Endpunkte bereit.

## Tages-KMZ erzeugen

```bash
curl "http://localhost:8080/plugins/user-logbuch/api/exportKmz?date=2026-05-24"

Ohne Datum wird der aktuelle UTC-Tag verwendet:

curl "http://localhost:8080/plugins/user-logbuch/api/exportKmz"

Antwort enthält eine Job-ID:

{
  "status": "OK",
  "message": "KMZ export started.",
  "job": {
    "id": "...",
    "type": "daily-kmz",
    "status": "RUNNING"
  }
}
Törn-KMZ erzeugen
curl "http://localhost:8080/plugins/user-logbuch/api/exportTripKmz?from=2026-05-21&to=2026-05-24"
Jobstatus abfragen

Alle Jobs:

curl "http://localhost:8080/plugins/user-logbuch/api/exportStatus"

Ein einzelner Job:

curl "http://localhost:8080/plugins/user-logbuch/api/exportStatus?job=JOB_ID"
Ausgabeorte

Tages-KMZ:

AVNAV_DATA_DIR/overlays/YYYYMMDD_logbuch.kmz

Törn-KMZ:

AVNAV_DATA_DIR/overlays/YYYYMMDD-YYYYMMDD_toern_logbuch.kmz
Asynchrones Verhalten

Der Export läuft in einem Hintergrundthread.

Vorteile:

AVNav blockiert nicht
WebUI bleibt bedienbar
größere Törndateien können erzeugt werden
Status kann später abgefragt werden
Benötigte Tools

Die Export-Scripts werden durch tools/install_or_update.sh installiert nach:

AVNAV_DATA_DIR/logbook-tools

Darin liegen unter anderem:

export_additional_kmz.py
export_trip_kmz.py
common.py
kmz-icons/


## Overlay-Buttons

Das Logbuch-Overlay enthält kleine Export-Buttons:

```text
KMZ Heute
Törn 7 Tage
KMZ Heute

Startet asynchron den Export für den aktuellen UTC-Tag.

API:

/api/exportKmz

Ausgabe:

AVNAV_DATA_DIR/overlays/YYYYMMDD_logbuch.kmz
Törn 7 Tage

Startet asynchron den Törnexport für die letzten 7 Tage.

API:

/api/exportTripKmz?from=YYYY-MM-DD&to=YYYY-MM-DD

Ausgabe:

AVNAV_DATA_DIR/overlays/YYYYMMDD-YYYYMMDD_toern_logbuch.kmz
Statusanzeige

Das Overlay zeigt kompakt:

Export startet...
Export läuft...
Export fertig
Export fehlgeschlagen


## Overlay-Buttons

Das Logbuch-Overlay enthält kleine Export-Buttons:

```text
KMZ Heute
Törn 7 Tage
KMZ Heute

Startet asynchron den Export für den aktuellen UTC-Tag.

API:

/api/exportKmz

Ausgabe:

AVNAV_DATA_DIR/overlays/YYYYMMDD_logbuch.kmz
Törn 7 Tage

Startet asynchron den Törnexport für die letzten 7 Tage.

API:

/api/exportTripKmz?from=YYYY-MM-DD&to=YYYY-MM-DD

Ausgabe:

AVNAV_DATA_DIR/overlays/YYYYMMDD-YYYYMMDD_toern_logbuch.kmz
Statusanzeige

Das Overlay zeigt kompakt:

Export startet...
Export läuft...
Export fertig
Export fehlgeschlagen


## Törn Start / Törn Ende

Das Logbuch-Overlay enthält zusätzlich kleine Buttons:

```text
Törn Start
Törn Ende

Diese erzeugen normale Logbuch-Events:

trip_start
trip_end

Die Events verändern keinen Motor-/Segel-/Ankerstatus.

Sie werden mit Zeitstempel und aktueller Position gespeichert und erscheinen später als Marker in Tages- und Törn-KMZ-Dateien.

## Törn Start / Törn Ende

Das Logbuch-Overlay enthält zusätzlich kleine Buttons:

```text
Törn Start
Törn Ende

Diese erzeugen normale Logbuch-Events:

trip_start
trip_end

Die Events verändern keinen Motor-/Segel-/Ankerstatus.

Sie werden mit Zeitstempel und aktueller Position gespeichert und erscheinen später als Marker in Tages- und Törn-KMZ-Dateien.

## Törn Export Auswahl

Der Button heißt:

```text
Törn Export

Beim Klick fragt das Overlay:

1 = letzte 7 Tage
2 = seit letztem Törn Start
Export seit letztem Törn Start

Bei Auswahl 2 sucht das Plugin den letzten gespeicherten Logbucheintrag:

trip_start

Danach wird gesucht, ob nach diesem Start ein Eintrag existiert:

trip_end

Verhalten:

trip_start vorhanden, trip_end vorhanden:
→ Export von Törn Start bis Törn Ende

trip_start vorhanden, trip_end fehlt:
→ Export von Törn Start bis heute

kein trip_start vorhanden:
→ Fehlermeldung

API:

curl "http://localhost:8080/plugins/user-logbuch/api/exportCurrentTripKmz"

Die erzeugte KMZ wird wie alle Overlays nach AVNAV_DATA_DIR/overlays/ geschrieben und vorhandene Dateien werden überschrieben.

## Fehlende Tagesdaten

Wenn für einen Tag keine Logbuchdatei existiert, wird im Overlay eine verständliche Meldung angezeigt:

```text
Keine Logbucheinträge für diesen Tag.

Wenn keine GPX-Trackdatei existiert:

Keine GPX-Trackdatei für diesen Tag.

Der Export läuft weiter asynchron, aber der Job endet mit Status ERROR und einer lesbaren message.

## Fehlende Tagesdaten

Wenn für einen Tag keine Logbuchdatei existiert, wird im Overlay eine verständliche Meldung angezeigt:

```text
Keine Logbucheinträge für diesen Tag.

Wenn keine GPX-Trackdatei existiert:

Keine GPX-Trackdatei für diesen Tag.

Der Export läuft weiter asynchron, aber der Job endet mit Status ERROR und einer lesbaren message.

## Fehlende Tagesdaten

Wenn für einen Tag keine Logbuchdatei existiert, wird im Overlay eine verständliche Meldung angezeigt:

```text
Keine Logbucheinträge für diesen Tag.

Wenn keine GPX-Trackdatei existiert:

Keine GPX-Trackdatei für diesen Tag.

Der Export läuft weiterhin asynchron. Der Job endet mit Status ERROR, liefert aber eine lesbare message.

## Fehlende Tagesdaten

Wenn für einen Tag keine Logbuchdatei existiert, wird im Overlay eine verständliche Meldung angezeigt:

```text
Keine Logbucheinträge für diesen Tag.

Wenn keine GPX-Trackdatei existiert:

Keine GPX-Trackdatei für diesen Tag.

Der Export läuft weiterhin asynchron. Der Job endet mit Status ERROR, liefert aber eine lesbare message.
