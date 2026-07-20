# AVNav Logbuch Plugin v1.9.0

## HTML-Tagesbericht

- Neuer HTML-Tagesexport direkt aus jeder Tagesansicht
- Bericht wird bei Bedarf erzeugt und unmittelbar heruntergeladen
- Keine dauerhafte Sammlung bereits erzeugter HTML-Dateien
- DIN-A4-optimiertes Layout mit 8 mm Seitenrand
- Kompakte Tagesstatistik für Segel-, Motor- und Gesamtfahrt
- Strecke, Zeit, Höchstgeschwindigkeit und Durchschnittsgeschwindigkeit
- Dezente Tabellenflächen und vollständig hervorgehobene Gesamtzeile
- Darstellung der Logbucheinträge, Ankerplätze und Notizen
- Vorbereitung für spätere Schiffs-, Crew- und Törndaten

## Kartenansicht

- Statische SVG-Karte direkt in der HTML-Datei eingebettet
- Farbige Trackabschnitte für Motor, Segel und unbekannten Zustand
- Start-, Ziel-, Anker- und Logbuchmarker
- Optionaler OSM- und OpenSeaMap-Hintergrund
- Lokaler Kartenkachel-Cache
- Vollständig funktionsfähiger Offline-Fallback mit blau strukturierter Fläche
- HTML-Export wird auch ohne Internetverbindung und Kartenhintergrund erzeugt
- Keine zusätzliche verpflichtende Python-Abhängigkeit

## Gemeinsame Export-Engine

- Gemeinsame Navigations- und Statistikbasis für HTML-, Tages-KMZ- und Törn-KMZ-Export
- Eindeutige Klassifizierung der Tracksegmente
- Keine doppelte Zählung bei gleichzeitig aktivem Motor und Segel
- Gesamtstrecke basiert auf dem vollständigen gültigen Track
- Höchst- und Durchschnittsgeschwindigkeiten ergänzt
- Unbekannte Trackabschnitte werden separat ausgewertet
- Tages- und Törn-KMZ deutlich bereinigt und auf gemeinsame Module umgestellt
- Alte doppelte Berechnungslogik entfernt

## Qualitätssicherung

- Unit-Tests für Zustandsrekonstruktion und Navigation
- Unit-Tests für statische Kartenprojektion
- Unit-Tests für den HTML-Tagesexport
- Bereinigung einer fehlerhaften Warnung beim ersten Statusereignis
- Release-Paket enthält nun die vollständige Export-Engine und alle Renderer


# v1.8.0

## Neue Funktionen

- Logbucheinträge können direkt in der Detailansicht dupliziert werden
- Neue Einträge können vor oder nach einem bestehenden Eintrag eingefügt werden
- Duplizierte Einträge erhalten beim Speichern eine neue eindeutige ID
- Eingefügte Einträge können vor dem Speichern vollständig bearbeitet werden
- Beim Ändern des Zeitstempels wird die Position anhand der AVNav-Trackdatei neu bestimmt

## Positionsbestimmung

- Positionsdaten werden aus den AVNav-AVT-Trackdateien gelesen
- Exakte Trackpunkte werden direkt übernommen
- Zwischen benachbarten Trackpunkten kann die Position interpoliert werden
- Alternativ kann ein zeitlich naher Trackpunkt verwendet werden
- Einträge werden auch dann gespeichert, wenn keine Trackposition verfügbar ist
- Fehlende Positionen werden eindeutig als `unknown` gekennzeichnet

## Historie und Status

- Neue und bearbeitete Einträge werden in die chronologische Historie einsortiert
- Motor-, Segel- und Ankerstatus werden nach Änderungen vollständig neu berechnet
- Ungültige Statusfolgen erzeugen weiterhin eine Warnung
- Das erzwungene Speichern trotz Warnung bleibt möglich

## Benutzeroberfläche

- Neue Aktionen:
  - Duplizieren
  - Davor einfügen
  - Danach einfügen
- Gemeinsames Bearbeitungsformular für neue, duplizierte und vorhandene Einträge
- Anzeige, dass für neue Einträge beim Speichern eine neue ID erzeugt wird

## Technische Änderungen

- Neuer AVT-Parser im Backend
- Positionsauflösung und Winkelinterpolation für Kursdaten
- Erweiterung der Add-API um die optionale Positionsauflösung
- Erneute Positionsbestimmung beim Ändern eines Zeitstempels

## 2.0.0 – Einheitliche Logbuch-Struktur

- Vollständige Umstellung auf die Benennung `logbuch`.
- Einmalige automatische Migration für Installationen bis Version 1.9.x.
- Vorhandene JSONL-Rohdaten werden in das neue Verzeichnis und Namensformat verschoben.
- Alte Plugin-, Daten- und Werkzeugverzeichnisse werden nach der Datenübernahme entfernt.
- AVNav wird ausschließlich nach dieser einmaligen Migration neu gestartet.
- Spätere Updates innerhalb der 2.x-Reihe lösen weder Migration noch Neustart aus.
