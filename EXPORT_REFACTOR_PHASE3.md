# Export-Refactoring – Phase 3

## Ziel

Statische, selbständige Kartenansicht für den späteren HTML-Tagesexport.

## Eigenschaften

- SVG-Ausgabe ohne zusätzliche Pflichtmodule
- vollständig offline funktionsfähig
- optionales Laden von OSM- und OpenSeaMap-Kacheln
- lokaler Kachelcache
- Fallback auf blau strukturierten Kartenhintergrund
- Trackdarstellung für Segel, Motor und unbekannte Abschnitte
- Start- und Zielmarkierung
- Anker- und Logbuchmarker
- automatische Projektion des Tracks auf eine rechteckige Fläche
- Kartenfehler dürfen den späteren HTML-Export nicht abbrechen

## Dateien

- `tools/renderers/render_static_map.py`
- `tools/test_static_map.py`

## Test

```bash
cd ~/avnav-logbook-plugin
PYTHONPATH=tools python3 -m unittest tools/test_static_map.py
```

## Offline-Test mit vorhandenen Testdaten

```bash
PYTHONPATH=tools python3 - <<'PY'
from pathlib import Path
from exportlib.export_model import load_day
from renderers.render_static_map import render_static_map

model = load_day(
    Path('testdata/avnav-data/logbook'),
    Path('testdata/avnav-data/tracks'),
    '2026-06-01',
)
svg = render_static_map(model, online=False)
Path('/tmp/logbuch-export-test/track-offline.svg').write_text(svg, encoding='utf-8')
print('/tmp/logbuch-export-test/track-offline.svg')
PY
```
