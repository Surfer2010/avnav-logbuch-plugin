Strategie
1. JSONL bleibt die primäre lokale Quelle

Vorteile:

- robust
- offlinefähig
- einfach zu sichern
- leicht nach InfluxDB/CSV/GeoJSON exportierbar
2. InfluxDB wird Analyse-/Dashboard-Ziel

InfluxDB eignet sich für:

- Zeitreihen
- Motor an/aus
- Segel gesetzt/eingeholt
- Anker ab/auf
- Tages-/Wochen-/Trip-Auswertungen
- Grafana Dashboards
3. Karten-Auswertung besser separat

Für Karten ist InfluxDB nur bedingt ideal. Besser:

JSONL → GeoJSON Export → Leaflet/OpenLayers Karte

Damit möglich:

- Ankerpunkte als Marker
- Motorstrecken rot
- Segelstrecken grün
- Tripweise Darstellung
Datenmodell-Erweiterung

Nächste sinnvolle Felder:

{
  "timestamp": "2026-05-21T19:29:47Z",
  "event_type": "motor_on",
  "text": "",
  "lat": 54.123456,
  "lon": 10.123456,
  "sog": 4.8,
  "cog": 123.0,
  "trip_id": "2026-05-21",
  "source": "avnav-logbuch-plugin"
}
Auswertungslogik
Motorstunden
motor_on → motor_off = Motorlaufzeit
Segelstunden
sail_set → sail_down = Segelzeit
Ankerzeit
anchor_down → anchor_up = Ankerzeit
Karte
zwischen motor_on und motor_off → rote Linie
zwischen sail_set und sail_down → grüne Linie
anchor_down → Marker


InfluxDB als Analyseziel

InfluxDB wird optional als zusätzliches Ziel genutzt.

Geeignet für:

Zeitreihen
Statuswechsel
Tages-/Wochen-/Trip-Zeiträume
Grafana Dashboards
Motor-/Segel-/Ankerzeiten

Nicht ideal für:

komplexe Kartenlogik
GeoJSON-Export
nachträgliche semantische Trip-Zuordnung
GeoJSON für Karten

Für Karten wird ein separater Export empfohlen:

JSONL → Auswertescript → GeoJSON

Damit können Karten mit Leaflet oder OpenLayers dargestellt werden.

Datenmodell

Aktuelles Mindestmodell:

{
  "timestamp": "2026-05-21T19:29:47Z",
  "event_type": "motor_on",
  "text": "",
  "lat": null,
  "lon": null,
  "source": "avnav-logbuch-plugin"
}

Geplante Erweiterung:

{
  "timestamp": "2026-05-21T19:29:47Z",
  "event_type": "motor_on",
  "text": "",
  "lat": 54.123456,
  "lon": 10.123456,
  "sog": 4.8,
  "cog": 123.0,
  "heading": 121.0,
  "trip_id": "2026-05-21",
  "source": "avnav-logbuch-plugin"
}
Eventtypen
Motor
motor_on
motor_off

Auswertung:

motor_on bis motor_off = Motorlaufzeit
Segel
sail_set
sail_down

Auswertung:

sail_set bis sail_down = Segelzeit
Anker
anchor_down
anchor_up

Auswertung:

anchor_down bis anchor_up = Ankerzeit
Freitext
manual

Auswertung:

manuelle Notizen, nicht automatisch zeitbildend
Auswertungen
Tagesauswertung

Pro Kalendertag:

Motorzeit
Segelzeit
Ankerzeit
Anzahl Logbucheinträge
erste Position
letzte Position
Ankerpunkte
Wochenauswertung

Pro Kalenderwoche:

Summe Motorzeit
Summe Segelzeit
Summe Ankerzeit
Anzahl Trips
meistgenutzte Ankerplätze
Tripauswertung

Ein Trip kann später definiert werden durch:

trip_start
trip_end

oder automatisch durch:

erster Logbucheintrag des Tages
bis letzter Logbucheintrag des Tages

Besser ist langfristig ein eigener Button:

Trip starten
Trip beenden
Diagramme
Kuchendiagramm

Mögliche Anteile:

Motorzeit
Segelzeit
Ankerzeit
Sonstige Zeit
Balkendiagramm

Mögliche Darstellung:

Tag | Motorstunden | Segelstunden | Ankerzeit
Zeitlinie

Mögliche Darstellung:

08:00 Motor an
09:20 Segel gesetzt
13:45 Segel eingeholt
14:10 Anker ab
Kartenstrategie
Ankerpunkte
anchor_down mit gültiger Position = Marker auf Karte

Markerinhalt:

Zeitpunkt
Freitext
Dauer bis anchor_up
Koordinaten
Motorstrecken

Wenn Positionsdaten regelmäßig vorhanden sind:

motor_on bis motor_off = rote Linie
Segelstrecken
sail_set bis sail_down = grüne Linie
Technische Umsetzung

Exportformat:

GeoJSON

Beispielstruktur:

{
  "type": "FeatureCollection",
  "features": []
}

Frontend später:

Leaflet

oder:

OpenLayers
InfluxDB-Strategie
Measurement
avnav_logbuch
Tags
event_type
trip_id
source
Fields
lat
lon
sog
cog
text
Beispiel Line Protocol
avnav_logbuch,event_type=motor_on,source=avnav-logbuch-plugin lat=54.123456,lon=10.123456,text="Motor an"
Grafana Dashboards

Mögliche Panels:

Motorstunden pro Tag
Segelstunden pro Tag
Ankerzeit pro Tag
letzter Logbucheintrag
Tabelle aller Einträge
Kuchendiagramm Motor/Segel/Anker
Karte mit Ankerpunkten
Entwicklungsfahrplan
Phase 1: Datenqualität

Ziele:

GPS-Position robuster aus AVNav lesen
zusätzliche Navigationsdaten speichern
JSONL-Format stabilisieren
manuelle Testdaten ermöglichen

Aufgaben:

plugin.py erweitern
Felder sog, cog, heading ergänzen
Fehlerhandling verbessern
Beispiel-JSONL dokumentieren
Phase 2: Statusmodell

Ziele:

Motorstatus erkennen
Segelstatus erkennen
Ankerstatus erkennen
offene Zustände erkennen

Aufgaben:

Zustand im Plugin speichern
Status im Overlay anzeigen
doppelte Events optional warnen
z. B. motor_on verhindern, wenn Motor bereits an ist
Phase 3: Auswertescript

Ziele:

JSONL-Dateien auswerten
Zeitdifferenzen berechnen
Tages-/Wochen-/Trip-Zusammenfassung erzeugen

Geplante Datei:

tools/analyze_logbuch.py

Ausgabeformate:

CSV
JSON
Markdown
Phase 4: GeoJSON Export

Ziele:

Ankerpunkte exportieren
Motorstrecken rot markieren
Segelstrecken grün markieren

Geplante Datei:

tools/export_geojson.py

Ausgabe:

exports/logbuch-map.geojson
Phase 5: InfluxDB

Ziele:

direkte InfluxDB-Schreibung stabilisieren
Offline-Fallback behalten
späterer Nachimport aus JSONL

Aufgaben:

Influx-Konfiguration dokumentieren
Retry-Strategie überlegen
Import-Script ergänzen

Geplante Datei:

tools/import_jsonl_to_influx.py
Phase 6: Grafana

Ziele:

Dashboard erstellen
Panels dokumentieren
Beispielqueries bereitstellen

Dokumentation:

docs/grafana-dashboard.md
Phase 7: Kartenansicht

Ziele:

Kartenansicht aus GeoJSON
Ankerpunkte als Marker
Motorstrecken rot
Segelstrecken grün

Mögliche Umsetzung:

standalone HTML mit Leaflet

oder später:

Integration in AVNav Plugin
Priorisierte nächste Schritte
plugin.py um zusätzliche Navigationsdaten erweitern
Test-GPS-Werte für LXC ermöglichen
Statusmodell für Motor, Segel und Anker einbauen
Auswertescript für Motor-/Segel-/Ankerzeiten erstellen
GeoJSON-Export erstellen
InfluxDB Import/Write stabilisieren
Grafana-Dashboard dokumentieren
Offene Designfragen
Soll ein Trip manuell gestartet/beendet werden?
Soll pro Tag automatisch ein Trip angenommen werden?
Soll ein Ankerpunkt bearbeitbar sein?
Sollen Logbucheinträge im Overlay editierbar sein?
Soll es Exportbuttons direkt im Plugin geben?
Soll InfluxDB direkt während der Fahrt beschrieben werden oder nur später synchronisiert werden?
EOF

## Direkt committen

```bash
git add docs/roadmap-data-analysis.md
git commit -m "Add roadmap for logbuch data analysis and InfluxDB"
git push
Empfohlener nächster technischer Schritt

Als nächstes würde ich Phase 1 umsetzen:

plugin.py erweitert speichern:
- lat/lon
- sog
- cog
- heading
- optional test_lat/test_lon für LXC

Danach kommt das erste Auswertescript:

tools/analyze_logbuch.py

Das kann dann direkt berechnen:

Motorzeit
Segelzeit
Ankerzeit
pro Tag

Und später daraus:

CSV
Markdown
Grafana/Influx
GeoJSON
