# AVNav Logbuch Plugin

<picture>
  <source
    media="(prefers-color-scheme: dark)"
    srcset="https://github.com/user-attachments/assets/7da8bc09-8c9e-46f3-b5f1-53fcc6b914ed">
  <source
    media="(prefers-color-scheme: light)"
    srcset="https://github.com/user-attachments/assets/7da8bc09-8c9e-46f3-b5f1-53fcc6b914ed">
  <img
    src="https://github.com/user-attachments/assets/7da8bc09-8c9e-46f3-b5f1-53fcc6b914ed"
    alt="AVNav Logbuch Plugin"
    width="128"
    height="128">
</picture>

Elektronisches Bord- und Törnlogbuch für [AVNav](https://www.wellenvogel.net/software/avnav/).

Das Plugin erfasst Ereignisse und Zustandsänderungen direkt aus der AVNav-Kartenansicht, ergänzt sie um verfügbare Navigationsdaten und bereitet daraus Tagesansichten, Törnauswertungen und Kartenexporte auf.

Die Daten bleiben vollständig lokal auf dem AVNav-System.

---

## Zielsetzung

### 1. Ereignisse während der Fahrt einfach erfassen

Das Plugin soll typische Bordereignisse wie Motor an oder aus, Segel gesetzt oder geborgen sowie Anker fallen oder auf unmittelbar während der Fahrt festhalten.

Die Bedienung erfolgt über frei platzierbare AVNav-Widgets und ein eigenes Overlay. Dadurch können Einträge direkt im Cockpit über Tablet oder Touchscreen erstellt werden, ohne dafür zum Kartentisch wechseln zu müssen.

### 2. Tagesfahrten und Törns dokumentieren

Aus den gespeicherten Ereignissen und Navigationsdaten entsteht ein digitales Logbuch für einzelne Tagesfahrten und mehrtägige Törns.

Die Daten können in praktikable Formate exportiert und durch Statistiken, Kartenansichten und chronologische Zusammenfassungen ergänzt werden.

---

## Funktionen

- frei platzierbare Widgets und Aktionsschaltflächen in der AVNav-Kartenansicht
- eigenes Overlay für Logbucheinträge und Statusänderungen
- Erfassung von Ereignissen mit Zeitstempel und GPS-Position
- Speicherung verfügbarer Navigationsdaten wie Kurs und Geschwindigkeit
- vordefinierte Ereignisse für Motor, Segel, Anker sowie Törnstart und Törnende
- Erfassung freier Textnotizen
- chronologische Tages- und Törnansicht
- Bearbeiten, Löschen, Duplizieren und nachträgliches Einfügen von Einträgen
- Rekonstruktion des aktuellen Motor-, Segel- und Ankerstatus
- Positionsbestimmung oder Interpolation aus vorhandenen AVNav-Trackdaten
- Export als HTML, KMZ, CSV und JSON
- gemeinsame Berechnungsgrundlage für Tagesberichte und Törnauswertungen
- vollständig lokale und offene Datenhaltung

---

## Umsetzung

### Dateneingabe

Daten werden über frei platzierbare Widgets in der AVNav-Kartenansicht sowie über die registrierte Logbuch-UserApp erfasst.

Direkt verfügbar sind:

- Motor an und aus
- Segel gesetzt und geborgen
- Anker fallen und auf
- Törn starten und beenden
- Freitextnotizen

Die Bedienung ist für Tablet, Touchscreen und den Einsatz im Cockpit optimiert.

### Datenspeicherung

Zu jedem Eintrag speichert das Plugin – soweit verfügbar:

- Zeitstempel
- Ereignistyp
- GPS-Position
- Kurs
- Geschwindigkeit
- Motorstatus
- Segelstatus
- Ankerstatus
- zusätzliche Notizen und Ereignisdaten

Die Rohdaten werden lokal in einem offenen JSONL-Format gespeichert. Eine verpflichtende Cloud oder externe Datenübertragung ist nicht vorgesehen.

### Datenausgabe und Export

Die Logbuch-UserApp zeigt alle Ereignisse chronologisch an und rekonstruiert daraus den jeweiligen Bordzustand.

Vorhandene Einträge können:

- bearbeitet
- gelöscht
- dupliziert
- davor oder danach eingefügt
- mit einem abweichenden Zeitstempel nachgetragen

werden.

Für nachträglich erfasste Ereignisse kann die Position aus den vorhandenen AVNav-Trackdaten übernommen oder interpoliert werden.

#### HTML-Tagesbericht

Für jeden Tag kann ein eigenständiger HTML-Bericht erzeugt werden. Dieser enthält unter anderem:

- Tagesstatistik
- Motor-, Segel- und Gesamtstrecke
- Fahrzeiten
- Durchschnitts- und Höchstgeschwindigkeit
- chronologische Ereignistabelle
- Notizen und Ankerplätze
- statische Kartenansicht
- farblich getrennte Trackabschnitte

Der Bericht bleibt auch ohne Internetverbindung verwendbar und kann auf jedes beliebige Endgerät heruntergeladen werden.

#### KMZ-Export

Das Plugin erzeugt Kartenoverlays für:

- Motorstrecken
- Segelstrecken
- unbekannte Streckenabschnitte
- Ankerpositionen
- Notizen
- Tagesfahrten
- mehrtägige Törns

Die KMZ-Dateien können unter anderem in AVNav, Google Earth und anderen KML/KMZ-kompatiblen Anwendungen verwendet werden.

#### CSV- und JSON-Export

CSV und JSON stellen die erfassten Rohdaten in maschinenlesbarer Form bereit. Dadurch können die Einträge außerhalb des Plugins weiterverarbeitet, archiviert oder in andere Systeme übernommen werden.

### Interne Datenhaltung

Die Datenhaltung und die Exportfunktionen verwenden eine gemeinsame Berechnungsbasis. Dadurch greifen Tagesansicht, HTML-Bericht, Kartenexporte und Törnauswertungen auf dieselben rekonstruierten Zustände und Streckenabschnitte zurück.

Wesentliche Eigenschaften:

- vollständig lokale Datenhaltung
- offene JSONL-Rohdaten
- nachvollziehbare Statusrekonstruktion
- gemeinsame Export-Engine
- asynchrone Exporte im Hintergrund
- keine verpflichtende Cloud

---

## Installation und Updates

### Installation über ein Release-ZIP

Die aktuelle ZIP-Datei kann auf der GitHub-Releases-Seite heruntergeladen werden.

Das ZIP enthält den vollständigen Pluginordner:

```text
logbuch/
```

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

### Installation über das Repository

```bash
cd /tmp
git clone https://github.com/Surfer2010/avnav-logbuch-plugin.git
cd avnav-logbuch-plugin
sudo bash tools/install_or_update.sh
```

Das Installationsskript erkennt den AVNav-Datenpfad, installiert das Plugin und kopiert die zugehörigen Werkzeuge.

### Update innerhalb der Version 2.x

```bash
cd ~/avnav-logbuch-plugin
git pull
sudo bash tools/install_or_update.sh
```

Updates innerhalb der Version-2.x-Reihe führen keine erneute Namensmigration und keinen migrationsbedingten Neustart aus.

### Update von Version 1.9.x oder älter

Version 2.0.0 führte eine einmalige Umstellung aller internen Namen und Pfade von `logbook` auf `logbuch` durch.

Beim ersten Update werden:

- vorhandene JSONL-Rohdaten übernommen
- alte Dateinamen umgestellt
- alte Plugin- und Datenpfade entfernt
- ein Migrationsmarker angelegt
- AVNav einmal neu gestartet

Vor diesem einmaligen Versionssprung wird eine Sicherung der vorhandenen JSONL-Dateien empfohlen.

Typischer Speicherort:

```text
/var/lib/avnav/logbuch/
```

Ab Version 2.0 wird ausschließlich die neue Benennung verwendet.

---

## Sonstiges

- Open Source
- direkte Integration in AVNav
- Touch- und Cockpitbedienung
- lokale Datenspeicherung
- offene Exportformate
- geeignet für private Tagesfahrten und mehrtägige Törns

### Screenshots

#### AVNav-Widgets

<!--
![AVNav Logbuch Widgets](docs/images/logbuch-widgets.png)
-->

#### Logbuchansicht

<!--
![Logbuch Tagesansicht](docs/images/logbuch-tagesansicht.png)
-->

#### HTML-Tagesbericht

<!--
![HTML Tagesbericht](docs/images/logbuch-html-export.png)
-->

#### Karten- und Törnexport

<!--
![KMZ Törnexport](docs/images/logbuch-kmz-export.png)
-->
