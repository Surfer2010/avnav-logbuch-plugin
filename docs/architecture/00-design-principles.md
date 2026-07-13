# Design Principles

## Ziel

Das AVNav-Logbuch-Plugin soll sich von einer Sammlung einzelner Buttons zu einer generischen Event-Engine entwickeln.

Alle zukünftigen Funktionen sollen auf einem gemeinsamen Datenmodell aufbauen.

---

# Grundprinzipien

## 1. Event First

Das Logbuch besteht aus Ereignissen (Events).

Ein Event beschreibt:

- Was ist passiert?
- Wann ist es passiert?
- Wo ist es passiert?
- Welche Zusatzinformationen gehören dazu?

Alle weiteren Auswertungen basieren ausschließlich auf diesen Events.

---

## 2. Track und Events sind getrennt

Ein Track beschreibt den gefahrenen Weg.

Ein Event beschreibt ein Ereignis.

Ein Event ersetzt niemals einen Trackpunkt.

Ein Track entsteht nicht aus den Events.

Beide Datenquellen werden erst während eines Exports oder einer Auswertung zusammengeführt.

---

## 3. Einmal erfassen – mehrfach verwenden

Jedes Event soll nur einmal gespeichert werden.

Darauf greifen später zu:

- KMZ
- Markdown
- CSV
- PDF
- HTML
- Statistiken
- Reiseberichte

Exporter interpretieren keine Rohdaten, sondern arbeiten mit normalisierten Events.

---

## 4. Rückwärtskompatibilität

Bereits gespeicherte Logbücher müssen weiterhin lesbar bleiben.

Neue Versionen dürfen ältere JSONL-Dateien nicht unbrauchbar machen.

Neue Felder werden ergänzt, nicht vorausgesetzt.

---

## 5. Erweiterbarkeit

Neue Eventtypen dürfen möglichst keinen bestehenden Code verändern.

Neue Informationen werden grundsätzlich unter `details` gespeichert.

---

## 6. Konfiguration vor Hardcoding

Neue Buttons, Aktionen und Dialoge sollen langfristig konfigurierbar sein.

Das Ziel ist:

- weniger JavaScript
- weniger Sonderfälle
- bessere Erweiterbarkeit

---

## 7. Kleine, nachvollziehbare Commits

Architekturänderungen erfolgen in kleinen Schritten.

Jeder Commit soll:

- lauffähig
- testbar
- verständlich

sein.

---

## 8. Dokumentation gehört zur Entwicklung

Neue Architekturentscheidungen werden dokumentiert.

Die Dokumentation beschreibt das Zielsystem und dient als Referenz für zukünftige Entwicklungen.

---

## Langfristige Vision

Das Plugin entwickelt sich zu einer generischen Event-Engine für AVNav.

Das Logbuch ist dabei nur eine von mehreren möglichen Darstellungen der gespeicherten Ereignisse.