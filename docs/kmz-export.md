
KMZ Export

Der KMZ Export kombiniert:

AVNav GPX Tagestrack
+
AVNav Logbuch JSONL

zu:

YYYYMMDD_logbuch.kmz
Enthaltene Daten
Motorstrecken
Segelstrecken
Ankerpunkte
Logbuchnotizen
Tagesstatistik
eingebettete Icons
Dateiinhalt

Eine KMZ ist eine ZIP-Datei:

YYYYMMDD_logbuch.kmz
├── doc.kml
└── icons/
    ├── anchor.png
    └── note.png
KML Farben

Motor:

rot

Segel:

grün
Datenquellen

Logbuch:

/home/pi/avnav/data/logbook/YYYYMMDD_logbuch.jsonl

Legacy wird unterstützt:

/home/pi/avnav/data/logbook/logbook-YYYY-MM-DD.jsonl

Track:

/home/pi/avnav/data/overlays/YYYY-MM-DD.gpx
Google Earth

Die erzeugte KMZ kann in Google Earth geöffnet werden.

Sie enthält eingebettete Icons und benötigt dafür keine externen Google-Icon-URLs.

## Distanzberechnung

Der KMZ-Export berechnet für Motor- und Segelabschnitte die Distanz.

Grundlage sind die GPX-Trackpunkte innerhalb des jeweiligen Logbuch-Intervalls.

Berechnung:

```text
Punkt 1 → Punkt 2
Punkt 2 → Punkt 3
Punkt 3 → Punkt 4
...
Summe = Distanz

Die Einzelabstände werden mit der Haversine-Formel berechnet.

Ausgabe je Abschnitt:

Distanz: 1.23 sm
Durchschnitt: 4.56 kn
Trackpunkte: 42

Zusätzlich werden Tageswerte erzeugt:

Motordistanz
Segeldistanz
Gesamtdistanz
TimeSpan / Zeitleiste

Motor- und Segelabschnitte enthalten KML-TimeSpan-Elemente:

<TimeSpan>
  <begin>2026-05-24T06:41:33Z</begin>
  <end>2026-05-24T07:46:06Z</end>
</TimeSpan>

Ankerpunkte und Logbuchnotizen enthalten TimeStamp:

<TimeStamp>
  <when>2026-05-24T07:45:58Z</when>
</TimeStamp>

Google Earth kann diese Informationen für die Zeitleiste nutzen.

Törn-Marker

Folgende Events werden als Marker in der KMZ dargestellt:

trip_start
trip_end

Sie dienen zur Markierung von Törnbeginn und Törnende.

Sie verändern keine Statuslogik.

Törn-Marker

Folgende Events werden als Marker in der KMZ dargestellt:

trip_start
trip_end

Sie dienen zur Markierung von Törnbeginn und Törnende.

Sie verändern keine Statuslogik.

Törn Start als Exportgrenze

Die Events:

trip_start
trip_end

werden nicht nur als Marker gespeichert, sondern können auch als Grenzen für den Törnexport genutzt werden.

Der API-Endpunkt:

/api/exportCurrentTripKmz

exportiert den Zeitraum:

letzter trip_start → nächster trip_end

oder, falls kein Törn Ende vorhanden ist:

letzter trip_start → heute

