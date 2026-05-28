# Pfade und automatische Erkennung

Die Tools verwenden eine zentrale Pfaderkennung in:

```text
tools/common.py
Erkennungsreihenfolge
expliziter Parameter --avnav-data
Umgebungsvariable AVNAV_DATA_DIR
/home/pi/avnav/data
/var/lib/avnav
Live-System

Typischer Pfad:

/home/pi/avnav/data
Debian/Test-LXC

Typischer Pfad:

/var/lib/avnav

Optional kann der Live-Pfad auf dem Testsystem simuliert werden:

mkdir -p /home/pi/avnav
ln -s /var/lib/avnav /home/pi/avnav/data

Prüfen:

ls -lah /home/pi/avnav/data/logbuch
ls -lah /home/pi/avnav/data/tracks
Umgebungsvariable

Alternativ:

export AVNAV_DATA_DIR=/var/lib/avnav

Danach können Tools ohne --avnav-data aufgerufen werden:

python3 tools/export_additional_kmz.py --date 2026-05-24
Verzeichnisstruktur
AVNAV_DATA_DIR/
├── logbuch/
│   ├── YYYYMMDD_logbuch.jsonl
│   └── logbuch-YYYY-MM-DD.jsonl
├── tracks/
│   ├── YYYY-MM-DD.gpx
│   └── YYYYMMDD_logbuch.kmz
└── plugins/
    └── logbuch/

