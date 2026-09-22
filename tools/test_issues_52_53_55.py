#!/usr/bin/env python3

from pathlib import Path


repo = Path(__file__).resolve().parent.parent

index = (
    repo / "logbuch/index.html"
).read_text(encoding="utf-8")

view = (
    repo / "logbuch/logbuch-view.js"
).read_text(encoding="utf-8")

mjs = (
    repo / "logbuch/plugin.mjs"
).read_text(encoding="utf-8")

backend = (
    repo / "logbuch/plugin.py"
).read_text(encoding="utf-8")

renderer = (
    repo / "tools/renderers/render_daily_html.py"
).read_text(encoding="utf-8")

event_types = (
    repo / "tools/exportlib/event_types.py"
).read_text(encoding="utf-8")


checks = {
    "#52 Today verwendet aktuelle Uhrzeit":
        '''if (offsetDays === 0) {
        end = now;''' in view,

    "#52 Today ruft setTodayRange(0)":
        '''if (range === "today") {
                setTodayRange(0);''' in view,

    "#53 UI Festmachen":
        '"Festmachen"' in mjs,

    "#53 UI Ablegen":
        '"Ablegen"' in mjs,

    "#53 View Festmachen":
        'title: "Festmachen"' in view,

    "#53 View Ablegen":
        'title: "Ablegen"' in view,

    "#53 Backend Festmachen":
        "'on': 'Festmachen'" in backend,

    "#53 Backend Ablegen":
        "'off': 'Ablegen'" in backend,

    "#53 HTML Festmachen":
        '"anchor_down": "Festmachen"' in renderer,

    "#53 HTML Ablegen":
        '"anchor_up": "Ablegen"' in renderer,

    "#53 Eventtypen Festmachen":
        '"label": "Festmachen"' in event_types,

    "#53 Eventtypen Ablegen":
        '"label": "Ablegen"' in event_types,

    "#55 kein Aktueller-Törn-Button":
        "export-current-trip" not in index,

    "#55 keine Button-Referenz":
        "exportCurrentTripButton" not in view,

    "#55 keine Trip-Schnellauswahl":
        'range === "trip"' not in view,

    "#54 Datumsspalte bleibt":
        "<th>Datum</th><th>Zeit</th>" in renderer,

    "Legacy trip_start bleibt":
        "trip_start" in backend,

    "Legacy trip_end bleibt":
        "trip_end" in backend,
}


failed = False

for name, ok in checks.items():
    print(
        "%-46s %s"
        % (
            name + ":",
            "OK" if ok else "FEHLT",
        )
    )

    if not ok:
        failed = True

if failed:
    raise SystemExit(
        "Regressionstest fehlgeschlagen"
    )

print()
print("Issues #52/#53/#54/#55: OK")
