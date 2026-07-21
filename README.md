# AVNav Logbuch Plugin
<img width="128" height="128" alt="logbuch-icon-128x128-light" src="https://github.com/user-attachments/assets/7da8bc09-8c9e-46f3-b5f1-53fcc6b914ed" />


Elektronisches Bord- und Törnlogbuch für [AVNav](https://www.wellenvogel.net/software/avnav/).

Das Plugin erfasst Motor-, Segel- und Ankerzustände direkt aus der AVNav-Kartenansicht, ergänzt sie um Navigationsdaten und bereitet daraus Tagesansichten, Törnauswertungen und Kartenexporte auf.

Die Daten bleiben vollständig lokal auf dem AVNav-System.

---

## Funktionen

### Logbucheinträge direkt in AVNav

Über frei platzierbare Widgets und ein eigenes Overlay können während der Fahrt Einträge erfasst werden:

- Motor an und aus
- Segel gesetzt und geborgen
- Anker fallen und auf
- Freitextnotizen
- Törn starten und beenden

Zu jedem Eintrag speichert das Plugin – soweit verfügbar:

- Zeitstempel
- GPS-Position
- Kurs
- Geschwindigkeit
- aktuellen Motor-, Segel- und Ankerstatus

Die Bedienung ist für Tablet, Touchscreen und Cockpit optimiert.

---

## Tages- und Törnansicht

Das Logbuch stellt alle Ereignisse chronologisch dar und rekonstruiert daraus den aktuellen Bordzustand.

Vorhandene Einträge können:

- bearbeitet
- gelöscht
- dupliziert
- davor oder danach eingefügt
- mit einem abweichenden Zeitstempel nachgetragen

werden.

Bei nachträglichen Einträgen kann die Position aus den vorhandenen AVNav-Trackdaten bestimmt oder interpoliert werden.

---

## Exporte und Auswertungen

### HTML-Tagesbericht

Für jeden Tag kann ein eigenständiger HTML-Bericht erzeugt werden.

Enthalten sind unter anderem:

- Tagesstatistik
- Motor-, Segel- und Gesamtstrecke
- Fahrzeiten
- Durchschnitts- und Höchstgeschwindigkeit
- Ereignistabelle
- Notizen und Ankerplätze
- statische Kartenansicht
- farblich getrennte Trackabschnitte

Der Bericht bleibt auch ohne Internetverbindung verwendbar.

### KMZ-Export

Das Plugin erzeugt Kartenoverlays für:

- Motorstrecken
- Segelstrecken
- unbekannte Streckenabschnitte
- Ankerpositionen
- Notizen
- Tagesfahrten
- mehrtägige Törns

Die KMZ-Dateien können unter anderem in AVNav, Google Earth und anderen KML/KMZ-kompatiblen Anwendungen verwendet werden.

### Weitere Exportgrundlagen

Die gemeinsame Export-Engine bildet die Grundlage für:

- HTML
- Tages-KMZ
- Törn-KMZ
- GPX
- zukünftige JSON- und CSV-Rohdatenexporte

---

## Besonderheiten

- vollständig lokale Datenhaltung
- keine verpflichtende Cloud
- direkte Integration in AVNav
- frei platzierbare AVNav-Widgets
- Touch- und Cockpitbedienung
- asynchrone Exporte im Hintergrund
- offene JSONL-Rohdaten
- nachvollziehbare Statusrekonstruktion
- gemeinsame Berechnungsbasis für alle Exporte
- Open Source

---

## Screenshots

### AVNav-Widgets

<!-- Screenshot einfügen:
![AVNav Logbuch Widgets](docs/images/logbuch-widgets.png)
-->

### Logbuchansicht

<!-- Screenshot einfügen:
![Logbuch Tagesansicht](docs/images/logbuch-tagesansicht.png)
-->

### HTML-Tagesbericht

<!-- Screenshot einfügen:
![HTML Tagesbericht](docs/images/logbuch-html-export.png)
-->

### Karten- und Törnexport

<!-- Screenshot einfügen:
![KMZ Törnexport](docs/images/logbuch-kmz-export.png)
-->

---

# Installation

## Installation über ein Release-ZIP

Die aktuelle ZIP-Datei kann auf der GitHub-Releases-Seite heruntergeladen werden.

Das ZIP enthält bereits den vollständigen Pluginordner:

```text
logbuch/

Je nach AVNav-Installation kann das ZIP direkt über die Pluginverwaltung hochgeladen oder manuell in das Pluginverzeichnis entpackt werden.

Typischer Zielpfad:

```text
/var/lib/avnav/plugins/logbuch/
```

Bei Raspberry-Pi-Installationen kann der Datenpfad beispielsweise lauten:

```text
/home/pi/avnav/data/plugins/logbuch/
```

Nach einer manuellen Installation muss AVNav einmal neu gestartet werden:

```bash
sudo systemctl restart avnav
```

---

## Installation über das Repository

```bash
cd /tmp
git clone https://github.com/Surfer2010/avnav-logbuch-plugin.git
cd avnav-logbuch-plugin

sudo bash tools/install_or_update.sh
```

Das Installationsskript erkennt den AVNav-Datenpfad, installiert das Plugin und kopiert die zugehörigen Werkzeuge.

---

# Update

## Update innerhalb der Version 2.x

Repository aktualisieren:

```bash
cd ~/avnav-logbuch-plugin
git pull
sudo bash tools/install_or_update.sh
```

Updates innerhalb der Version-2.x-Reihe führen keine erneute Namensmigration und keinen migrationsbedingten Neustart aus.

## Update von Version 1.9.x oder älter

Version 2.0.0 führte eine einmalige Umstellung aller internen Namen und Pfade von `logbook` auf `logbuch` durch.

Beim ersten Update werden:

* vorhandene JSONL-Rohdaten übernommen
* alte Dateinamen umgestellt
* alte Plugin- und Datenpfade entfernt
* ein Migrationsmarker angelegt
* AVNav einmal neu gestartet

Vor diesem einmaligen Versionssprung wird eine Sicherung der vorhandenen JSONL-Dateien empfohlen.

Typischer Speicherort:

```text
/var/lib/avnav/logbuch/
```

Ab Version 2.0 wird ausschließlich die neue Benennung verwendet.

---

# Datenhaltung

## Rohdaten

Die eigentlichen Logbuchdaten werden tageweise im JSONL-Format gespeichert:

```text
/var/lib/avnav/logbuch/logbuch-YYYY-MM-DD.jsonl
```

Jede Zeile enthält einen eigenständigen Logbucheintrag.

Typische Inhalte:

* eindeutige ID
* Ereignistyp
* Zeitstempel
* Position
* Kurs
* Geschwindigkeit
* Zusatzdaten
* Statusinformationen
* Freitext

Die JSONL-Dateien sind die maßgebliche Datenbasis. Exporte können daraus erneut erzeugt werden.

## Weitere AVNav-Daten

Für Auswertungen verwendet das Plugin zusätzlich vorhandene AVNav-Daten:

```text
tracks/
overlays/
logbuch/
logbuch-tools/
plugins/logbuch/
```

Bedeutung:

| Verzeichnis        | Inhalt                       |
| ------------------ | ---------------------------- |
| `logbuch/`         | dauerhafte JSONL-Rohdaten    |
| `tracks/`          | AVNav-Trackdaten             |
| `overlays/`        | erzeugte KMZ-Overlays        |
| `plugins/logbuch/` | installiertes Plugin         |
| `logbuch-tools/`   | Export- und Analysewerkzeuge |

---

# Verarbeitung

Der vereinfachte Datenfluss lautet:

```text
AVNav / GPS / NMEA
        │
        ▼
Logbucheintrag mit Zeit und Position
        │
        ▼
Tagesweise JSONL-Rohdaten
        │
        ├── Tagesansicht
        ├── Törnansicht
        ├── Statusrekonstruktion
        ├── HTML-Bericht
        ├── Tages-KMZ
        ├── Törn-KMZ
        └── weitere Exportformate
```

## Statusrekonstruktion

Motor-, Segel- und Ankerzustände werden chronologisch aus den gespeicherten Ereignissen rekonstruiert.

Dadurch können auch nachträglich eingefügte oder bearbeitete Einträge berücksichtigt werden.

Ungültige Zustandsfolgen werden erkannt und dem Benutzer als Warnung angezeigt.

## Trackauswertung

Für Strecken- und Kartenberechnungen werden vorhandene AVNav-Trackdaten ausgewertet.

Die gemeinsame Export-Engine:

* ordnet Trackabschnitte Motor, Segel oder unbekannt zu
* verhindert doppelte Streckenzählung
* berechnet Distanz und Fahrzeit
* bestimmt Durchschnitts- und Höchstgeschwindigkeit
* erzeugt eine einheitliche Datengrundlage für alle Exporte

## Asynchrone Exporte

Aufwendige Exporte laufen im Hintergrund. AVNav bleibt während der Verarbeitung bedienbar.

Der Status eines Exportauftrags kann über die Plugin-Schnittstelle abgefragt werden.

---

# Entwicklungsstand

Das Plugin wird aktiv weiterentwickelt.

Aktuelle Schwerpunkte:

* Stabilität und Datenintegrität
* bessere Dokumentation
* zusätzliche Rohdatenexporte
* Wetter- und Temperaturauswertungen
* erweiterte Törnstatistiken
* Boots-, Crew- und Segelprofile
* verbesserte Berichte und Visualisierungen

---

# Versionierung

Das Projekt verwendet [Semantic Versioning 2.0.0](https://semver.org/):

* **MAJOR:** inkompatible Struktur-, Speicher- oder API-Änderungen
* **MINOR:** neue rückwärtskompatible Funktionen
* **PATCH:** rückwärtskompatible Fehlerkorrekturen

---

# Lizenz

Dieses Projekt steht unter der in [`LICENSE`](LICENSE) angegebenen Open-Source-Lizenz.

```

Für die GitHub-Startseite würde ich zusätzlich direkt unter der Einleitung eine breite Übersichtsaufnahme der Logbuchansicht platzieren. Die drei weiteren Screenshots können kompakt unter „Screenshots“ folgen.
```




















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

## Installation ab v1.4.1

### Standardinstallation über AVNav

Für neue Installationen wird das Release-ZIP direkt in AVNav hochgeladen:

```text
logbuch-v1.4.1.zip
```

Das ZIP enthält bereits den korrekten Pluginordner:

```text
logbuch/
```

Ein separates Installationsscript ist für eine Neuinstallation nicht nötig.

### Manuelle Installation per CLI

```bash
cd /home/pi/avnav/data/plugins
unzip /pfad/zu/logbuch-v1.4.1.zip
sudo systemctl restart avnav
```

AVNav stellt das Plugin danach unter folgendem Pfad bereit:

```text
/plugins/user-logbuch/
```

### Einheitliche Benennung

Das Projekt verwendet ausschließlich `Logbuch` beziehungsweise `logbuch`. Alte englische Namen, Pfade und Dateinamen werden nicht unterstützt. Vor einem Update müssen bestehende Installationen auf die aktuelle Verzeichnis- und Dateistruktur gebracht werden.
