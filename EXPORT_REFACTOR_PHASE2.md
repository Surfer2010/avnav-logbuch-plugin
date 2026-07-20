# Export-Refactoring Phase 2

## Inhalt

- Korrektur der Anfangszustands-Rekonstruktion
- keine falsche `already active`-Warnung mehr beim ersten Start-Ereignis
- weiterhin Warnung bei echten doppelten Start-Ereignissen
- automatische Unit-Tests für Start-, Ende- und Doppelereignisse

## Test

```bash
cd ~/avnav-logbuch-plugin
PYTHONPATH=tools python3 -m unittest tools/test_navigation_analysis.py

PYTHONPATH=tools python3 tools/export_additional_kmz.py \
  --avnav-data ./testdata/avnav-data \
  --date 2026-06-01 \
  --output /tmp/20260601_logbuch.kmz
```
