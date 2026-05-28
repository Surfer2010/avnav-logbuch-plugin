# AVNav Logbuch Plugin

Erweitertes elektronisches Logbuch für AVNav mit Overlay, direkten Aktions-Widgets, GPX/KMZ-Export und Törn-Auswertung.

---

# Funktionen

## Elektronisches Logbuch direkt in AVNav

Das Plugin ergänzt AVNav um ein einfach bedienbares Bord- und Törnlogbuch.

Direkt aus der Kartenansicht können folgende Zustände erfasst werden:

- Motor an / aus (logbuch_b_motor...)
- Segel gesetzt / geborgen (logbuch_b_anker...)
- Anker fallen / auf (logbuch_b_segel...)
- (nur im Overlay) Freitext-Notizen
- (nur im Overlay) Törn Start / Ende
<img width="159" height="427" alt="grafik" src="https://github.com/user-attachments/assets/6c4cb255-21cb-40f9-9bbd-8df0a332e7a7" />


Alle Einträge werden zusammen mit Zeit und GPS-Position gespeichert.

---
# Installation
```
cd /tmp

rm -rf avnav-logbuch-plugin

git clone https://github.com/Surfer2010/avnav-logbuch-plugin.git

cd avnav-logbuch-plugin

cp logbuch/plugin.py /home/pi/avnav/data/plugins/user-logbuch/plugin.py
cp logbuch/plugin.js /home/pi/avnav/data/plugins/user-logbuch/plugin.js
cp logbuch/plugin.css /home/pi/avnav/data/plugins/user-logbuch/plugin.css

rm -rf /home/pi/avnav/data/logbuch-tools
mkdir -p /home/pi/avnav/data/logbuch-tools

cp -a tools/. /home/pi/avnav/data/logbuch-tools/

sudo chown -R pi:pi /home/pi/avnav/data/plugins/user-logbuch
sudo chown -R pi:pi /home/pi/avnav/data/logbuch-tools

sudo systemctl restart avnav
```
---

# Overlay Bedienung

Das Plugin besitzt ein eigenes Overlay innerhalb von AVNav. (logbuch_b_popup)
<img width="1118" height="674" alt="grafik" src="https://github.com/user-attachments/assets/54ffef2a-71cd-46ca-b713-f300efe80401" />

Das Overlay ermöglicht:

- schnelle Logbucheinträge
- Freitextnotizen
- Statuswechsel
- Törnverwaltung
- KMZ-Export direkt aus AVNav

Optimiert für:

- Tablet Bedienung
- Touchscreens
- Cockpit Nutzung
- Einhandbedienung unter Fahrt

---

# Frei platzierbare AVNav Widgets

Zusätzlich zum Overlay stellt das Plugin kompakte AVNav-Widgets bereit.

Diese können frei im AVNav Layout platziert werden:

- `logbuch_b_motor_an`
- `logbuch_b_motor_aus`
- `logbuch_b_segel_hoch`
- `logbuch_b_segel_runter`
- `logbuch_b_anker_ab`
- `logbuch_b_anker_auf`
- `logbuch_b_popup`

Die Widgets orientieren sich optisch an der nativen AVNav Benutzeroberfläche.

---

# GPX und Navigationsdaten

Zu jedem Eintrag werden Navigationsdaten gespeichert:

- Position
- Kurs
- Geschwindigkeit
- Zeitstempel

Zusätzlich können GPX-Daten ergänzt und ausgewertet werden.

---

# KMZ Export

Das Plugin kann automatisch KMZ Overlays erzeugen.

Die Dateien können direkt in AVNav als Overlay angezeigt werden.

Exportiert werden unter anderem:

- Motorstrecken
- Segelstrecken
- Ankerpositionen
- Logbuchnotizen
- Törnabschnitte
- Distanz
- Dauer
- Durchschnittsgeschwindigkeit
- Zeitachsen (KML TimeSpan)

Die KMZ-Dateien sind kompatibel mit:

- AVNav
- Google Earth
- OpenCPN
- KML/KMZ kompatiblen Kartenprogrammen

---

# Törn Export

Mehrtägige Törns können automatisch zusammengefasst werden.

Möglichkeiten:

- Export der letzten 7 Tage
- Export zwischen Törn Start und Törn Ende
- automatisches Überschreiben vorhandener Törn-KMZ Dateien

---

# Verzeichnisstruktur

Standardmäßig nutzt das Plugin:

```text
/home/pi/avnav/data/
````

Wichtige Verzeichnisse:

```text
logbuch/
tracks/
overlays/
plugins/
logbuch-tools/
```

---

# Asynchrone Exporte

KMZ-Exporte laufen asynchron im Hintergrund.

Dadurch bleibt AVNav während des Exports vollständig bedienbar.

Der aktuelle Status kann direkt über die Plugin API abgefragt werden.

---

# Ziel des Projekts

Das Ziel ist ein modernes, leicht bedienbares und vollständig lokales Bordlogbuch für Segler und Motorbootfahrer.

Fokus:

* einfache Bedienung
* Offlinefähigkeit
* Integration in AVNav
* offene Datenformate
* langfristige Archivierung
* vollständige lokale Datenhaltung

---

# Roadmap / Ausblick

Geplante Erweiterungen:

## GeoJSON Export

Zusätzlicher Export für:

* Grafana Geomap
* MediaWiki Karten
* Leaflet/OpenLayers
* Webkarten
* APIs

---

## Automatische Törnauswertung

Geplant:

* Hafen-Erkennung
* Ankerplatz-Erkennung
* Heatmaps
* Distanzstatistiken
* Segel-/Motor-Anteile
* automatische Tageszusammenfassungen

---

## Erweiterte Visualisierung

Geplant:

* Törn-Zeitleisten
* Wetterintegration
* Kartenmarker
* Live Status Widgets
* Dashboard Integration

---

## Statistik und Analyse

Mögliche spätere Funktionen:

* Motorstunden
* Segelstunden
* Hafenstatistik
* Nachtfahrten
* Durchschnittsgeschwindigkeit
* Langzeitstatistiken

---

# Entwicklungsstand

Das Projekt befindet sich aktiv in Entwicklung.

Der aktuelle Fokus liegt auf:

* Stabilität
* AVNav Integration
* Overlay Bedienung
* Exportfunktionen
* Touchoptimierung

---

## Versioning

This project follows Semantic Versioning 2.0.0:

- MAJOR: incompatible API or storage changes
- MINOR: new backwards compatible features
- PATCH: backwards compatible bugfixes

Stable releases should be safe to update within the same MAJOR version.

---

# Lizenz

Siehe LICENSE Datei im Repository.
