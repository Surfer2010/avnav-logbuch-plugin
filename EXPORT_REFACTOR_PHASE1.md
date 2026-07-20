# Export-Refactoring Phase 1

## Enthalten

- Gemeinsamer GPX-Reader in `tools/exportlib/read_tracks.py`
- Gemeinsame Formatierung in `tools/exportlib/formatting.py`
- Zentrale Zustands-, Segment- und Statistikberechnung in `tools/exportlib/navigation_analysis.py`
- Gemeinsames Tages-/Törn-Datenmodell in `tools/exportlib/export_model.py`
- Reiner KML/KMZ-Renderer in `tools/renderers/render_kml.py`
- Tages- und Törn-KMZ-Skripte als schlanke CLI-Einstiegspunkte

## Neue Berechnungsgrundlage

Jedes gültige Tracksegment wird genau einer Kategorie zugeordnet:

1. Motor aktiv → `motor`
2. Motor aus, Segel aktiv → `sail`
3. sonst → `unknown`

Dadurch werden Motor- und Segelstrecken nicht mehr doppelt gezählt. Die Gesamtstrecke wird direkt aus allen gültigen Tracksegmenten berechnet.

Je Kategorie werden Strecke, Zeit, Höchstgeschwindigkeit und Durchschnittsgeschwindigkeit bereitgestellt. Ungültige Segmente werden anhand großer Zeitlücken oder unplausibler Geschwindigkeit verworfen und als Warnung ausgegeben.

## Kompatibilität

- Produktivpfad `logbuch/` bleibt maßgeblich.
- Für vorhandene Testdaten wird zusätzlich der alte Ordner `logbuch/` gelesen.
- Bestehende CLI-Parameter und Ausgabedateinamen bleiben erhalten.
- `plugin.py` kann die Skripte weiterhin unverändert aufrufen.

## Lokale Tests

```bash
python3 -m py_compile \
  tools/exportlib/formatting.py \
  tools/exportlib/read_tracks.py \
  tools/exportlib/navigation_analysis.py \
  tools/exportlib/export_model.py \
  tools/renderers/render_kml.py \
  tools/export_additional_kmz.py \
  tools/export_trip_kmz.py

python3 tools/export_additional_kmz.py \
  --date 2026-06-01 \
  --avnav-data testdata/avnav-data \
  --output /tmp/test-day.kmz

python3 tools/export_trip_kmz.py \
  --from-date 2026-06-01 \
  --to-date 2026-06-01 \
  --avnav-data testdata/avnav-data \
  --output /tmp/test-trip.kmz
```

## Nächste Phase

- HTML-Tagesmodell und DIN-A4-Renderer
- statischer Kartenrenderer
- HTML-Download-Endpunkt und Exportauswahl im Frontend
- Vergleich realer alter/neuer KMZ-Werte und Grenzfalltests
