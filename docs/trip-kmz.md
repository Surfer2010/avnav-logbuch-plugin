# Multi-Day / Törn-KMZ

Der Törn-KMZ Export erzeugt eine gemeinsame KMZ-Datei für mehrere Tage.

## Aufruf

```bash
python3 tools/export_trip_kmz.py \
  --from-date 2026-05-21 \
  --to-date 2026-05-24 \
  --avnav-data /home/pi/avnav/data
Ausgabe
/home/pi/avnav/data/tracks/20260521-20260524_toern_logbuch.kmz
Inhalt

Die KMZ enthält:

Törnlogbuch
├── 2026-05-21
│   ├── Motorstrecken
│   ├── Segelstrecken
│   ├── Ankerpunkte
│   └── Logbuchnotizen
├── 2026-05-22
│   ├── Motorstrecken
│   ├── Segelstrecken
│   ├── Ankerpunkte
│   └── Logbuchnotizen
└── ...
Datenquellen je Tag

Logbuch:

logbook/YYYYMMDD_logbuch.jsonl

Fallback:

logbook/logbook-YYYY-MM-DD.jsonl

Track:

tracks/YYYY-MM-DD.gpx
Verhalten
Tage ohne Logbuchdatei werden übersprungen.
Tage ohne GPX-Datei werden übersprungen.
vorhandene Ausgabe-KMZ wird überschrieben.
Icons werden in die KMZ eingebettet.

Distanz und Zeitleiste

Der Törn-KMZ Export übernimmt die Distanzberechnung und TimeSpan/TimeStamp-Informationen aus dem Tagesexport.

Pro Tag und für den gesamten Törn werden zusammengefasst:

Motorzeit
Segelzeit
Motordistanz
Segeldistanz
Gesamtdistanz
Ankerpunkte
Logbuchnotizen

Motor- und Segelabschnitte besitzen TimeSpan-Elemente und können in Google Earth zeitlich gefiltert oder abgespielt werden.
