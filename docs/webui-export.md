# WebUI/API KMZ Export

Das Plugin stellt asynchrone Export-Endpunkte bereit.

## Tages-KMZ erzeugen

```bash
curl "http://localhost:8080/plugins/user-logbook/api/exportKmz?date=2026-05-24"

Ohne Datum wird der aktuelle UTC-Tag verwendet:

curl "http://localhost:8080/plugins/user-logbook/api/exportKmz"

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
curl "http://localhost:8080/plugins/user-logbook/api/exportTripKmz?from=2026-05-21&to=2026-05-24"
Jobstatus abfragen

Alle Jobs:

curl "http://localhost:8080/plugins/user-logbook/api/exportStatus"

Ein einzelner Job:

curl "http://localhost:8080/plugins/user-logbook/api/exportStatus?job=JOB_ID"
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

