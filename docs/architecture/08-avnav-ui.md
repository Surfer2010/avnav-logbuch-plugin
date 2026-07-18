# AVNav UI Architektur

## Ziel

Die AVNav-Oberfläche ist die primäre Benutzeroberfläche des digitalen Logbuchs.

Markdown, HTML, PDF und KMZ sind Exporte derselben Datenbasis.

## Datenfluss

JSONL
→ Event Reader
→ Document Builder
→ ViewModel
→ AVNav API
→ index.html (JavaScript)

## Standardansicht

- letzte 7 Tage
- Heute und Gestern geöffnet
- ältere Tage eingeklappt
- Navigation zu allen sichtbaren Tagen
- "Zurück nach oben" am Ende jedes Tages

## Live-Verhalten

- Daten werden bei Bedarf geladen (Lazy Loading)
- Nur der heutige Tag wird automatisch aktualisiert
- Bearbeitung erfolgt über Popups

## Geplante API

- GET /api/logbook/summary
- GET /api/logbook/day
- GET /api/logbook/status
- POST /api/logbook/event
- PUT /api/logbook/event
- DELETE /api/logbook/event
