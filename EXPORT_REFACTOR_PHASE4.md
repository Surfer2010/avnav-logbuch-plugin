# Export-Refactoring – Phase 4

## Inhalt

- eigenständiger HTML-Tagesbericht
- DIN-A4-Hochformat mit 8 mm Seitenrand und 194 mm Inhaltsbreite
- kompakte Statistik ohne sichtbare Tabellenlinien
- dezente Hinterlegung der Spalten- und Zeilenüberschriften
- vollständig fett gedruckte Gesamtzeile
- eingebettete statische SVG-Karte
- Online-Kartenkacheln nur optional
- Offline-Fallback mit strukturiertem blauem Hintergrund
- Logbucheinträge und Ankerplätze in kompakten Tabellen
- direkter Button `HTML herunterladen` in jeder Tagesansicht der UserApp
- HTML-Bericht wird erst beim Klick erzeugt
- temporäre Exportdatei mit automatischer Löschung nach fünf Minuten
- zusätzlicher HTML-Eintrag im bestehenden Exportdialog
- keine zusätzliche Pflichtabhängigkeit

## Test

```bash
PYTHONPATH=tools python3 -m unittest \
  tools/test_navigation_analysis.py \
  tools/test_static_map.py \
  tools/test_daily_html.py

PYTHONPATH=tools python3 tools/export_daily_html.py \
  --avnav-data ./testdata/avnav-data \
  --date 2026-06-01 \
  --offline-map \
  --output /tmp/logbuch-export-test/20260601_logbuch.html
```
