#!/usr/bin/env python3
"""Self-contained DIN-A4 daily HTML report renderer."""

import html
from datetime import timezone

from exportlib.formatting import format_hms
from renderers.render_static_map import render_map_placeholder, render_static_map

EVENT_LABELS = {
    "location": "Festmachen",
    "motor_on": "Motor an",
    "motor_off": "Motor aus",
    "sail_set": "Segel gesetzt",
    "sail_down": "Segel eingeholt",
    "anchor_down": "Anker ab",
    "anchor_up": "Anker auf",
    "manual": "Logbucheintrag",
    "trip_start": "Törnstart",
    "trip_end": "Törnende",
}


def _escape(value):
    return html.escape(str(value if value is not None else ""), quote=True)


def _format_decimal(value, digits=1):
    return f"{float(value or 0.0):.{digits}f}".replace(".", ",")


def _format_time(value):
    timestamp = value.get("_timestamp")
    if timestamp is None:
        return "--:--"
    return timestamp.astimezone(timezone.utc).strftime("%H:%M")


def _position_label(event):
    lat = event.get("lat")
    lon = event.get("lon")
    if lat is None or lon is None:
        return "–"
    return f"{float(lat):.5f}, {float(lon):.5f}"


def _statistics_table(statistics):
    rows = []
    for key, label, row_class in (
        ("sail", "Segel", ""),
        ("motor", "Motor", ""),
        ("total", "Gesamt", "total-row"),
    ):
        item = statistics[key]
        rows.append(
            f'<tr class="{row_class}">'
            f'<th scope="row">{label}</th>'
            f'<td>{_format_decimal(item["distance_nm"])} sm</td>'
            f'<td>{format_hms(item["duration_seconds"])}</td>'
            f'<td>{_format_decimal(item["max_speed_kn"])} kn</td>'
            f'<td>{_format_decimal(item["average_speed_kn"])} kn</td>'
            '</tr>'
        )
    return (
        '<table class="statistics-table" aria-label="Tagesstatistik">'
        '<colgroup><col class="row-label"><col><col><col><col></colgroup>'
        '<thead><tr><th></th><th>Strecke</th><th>Zeit</th>'
        '<th>Max. Geschw.</th><th>Durchschnitt</th></tr></thead>'
        f'<tbody>{"".join(rows)}</tbody></table>'
    )


def _count_strip(model):
    counts = model["statistics"]["counts"]
    return (
        '<dl class="count-strip">'
        f'<div><dt>Logbucheinträge</dt><dd>{counts.get("events", 0)}</dd></div>'
        f'<div><dt>Ankerplätze</dt><dd>{counts.get("anchorages", 0)}</dd></div>'
        f'<div><dt>Notizen</dt><dd>{counts.get("notes", 0)}</dd></div>'
        f'<div><dt>Unbekannte Strecke</dt><dd>{_format_decimal(model["statistics"]["unknown"]["distance_nm"])} sm</dd></div>'
        '</dl>'
    )


def _event_rows(events):
    rows = []
    for event in events:
        event_type = event.get("event_type") or "manual"
        label = EVENT_LABELS.get(event_type, event_type.replace("_", " ").title())
        text = (event.get("text") or "").strip()
        rows.append(
            '<tr>'
            f'<td class="time">{_format_time(event)}</td>'
            f'<td class="event">{_escape(label)}</td>'
            f'<td class="position">{_escape(_position_label(event))}</td>'
            f'<td class="description">{_escape(text) if text else "–"}</td>'
            '</tr>'
        )
    if not rows:
        rows.append('<tr><td colspan="4" class="empty">Keine Logbucheinträge vorhanden.</td></tr>')
    return "".join(rows)


def _anchor_rows(anchors):
    rows = []
    for index, event in enumerate(anchors, start=1):
        rows.append(
            '<tr>'
            f'<td>{index}</td><td>{_format_time(event)}</td>'
            f'<td>{_escape(_position_label(event))}</td>'
            f'<td>{_escape((event.get("text") or "").strip() or "–")}</td>'
            '</tr>'
        )
    return "".join(rows)


def render_daily_html(
    model,
    *,
    online_map=True,
    cache_dir=None,
    chart_xml=None,
    title=None,
    include_map=True,
):
    date_dash = model["date_dash"]
    report_title = title or f"Logbuch – Tagesbericht vom {date_dash}"
    map_section = ""

    if include_map:
        try:
            map_svg = render_static_map(
                model,
                cache_dir=cache_dir,
                chart_xml=chart_xml,
                online=online_map,
            )
        except Exception:
            map_svg = render_map_placeholder(
                message="Kartenansicht konnte nicht erzeugt werden"
            )

        map_section = (
            '<section class="map-frame" '
            'aria-label="Kartenansicht">'
            + map_svg
            + '</section>'
        )

    anchor_section = ""
    if model.get("anchors"):
        anchor_section = (
            '<section class="compact-section"><h2>Ankerplätze</h2>'
            '<table class="detail-table"><thead><tr><th>Nr.</th><th>Zeit</th>'
            '<th>Position</th><th>Bemerkung</th></tr></thead>'
            f'<tbody>{_anchor_rows(model["anchors"])}</tbody></table></section>'
        )

    return f'''<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{_escape(report_title)}</title>
<style>
@page {{ size: A4 portrait; margin: 8mm; }}
* {{ box-sizing: border-box; }}
html {{ background: #eef1f3; }}
body {{ margin: 0; color: #17232b; font-family: Arial, Helvetica, sans-serif; font-size: 9pt; }}
.report {{ width: 194mm; max-width: 194mm; margin: 8mm auto; padding: 0; background: #fff; }}
h1 {{ margin: 0 0 2.5mm; font-size: 17pt; line-height: 1.15; }}
h2 {{ margin: 3.5mm 0 1.5mm; font-size: 11pt; }}
.future-vessel-data {{ display: none; }}
.statistics-table {{ width: 100%; table-layout: fixed; border-collapse: separate; border-spacing: 0 1.25mm; font-size: 9pt; }}
.statistics-table .row-label {{ width: 20%; }}
.statistics-table th, .statistics-table td {{ border: 0; padding: 1.6mm 2.2mm; white-space: nowrap; }}
.statistics-table thead th {{ background: #e5eaed; font-weight: 600; text-align: right; }}
.statistics-table thead th:first-child {{ background: transparent; }}
.statistics-table tbody th {{ background: #edf1f3; font-weight: 500; text-align: left; }}
.statistics-table tbody td {{ text-align: right; }}
.statistics-table .total-row > * {{ font-weight: 700; }}
.count-strip {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 2mm; margin: 1.5mm 0 3mm; }}
.count-strip div {{ display: flex; justify-content: space-between; gap: 2mm; padding: 1.4mm 2mm; background: #f3f5f6; }}
.count-strip dt {{ color: #45535c; }} .count-strip dd {{ margin: 0; font-weight: 700; white-space: nowrap; }}
.map-frame {{ margin: 0 0 3mm; border: 0.25mm solid #b7c1c7; overflow: hidden; background: #d8eef8; }}
.map-frame svg {{ display: block; width: 100%; height: auto; max-height: 88mm; }}
.detail-table {{ width: 100%; border-collapse: collapse; table-layout: fixed; font-size: 8.4pt; }}
.detail-table th {{ padding: 1.3mm 1.5mm; background: #e5eaed; text-align: left; font-weight: 600; }}
.detail-table td {{ padding: 1.25mm 1.5mm; border-bottom: 0.2mm solid #d9dfe2; vertical-align: top; overflow-wrap: anywhere; }}
.entries-table .time {{ width: 12%; white-space: nowrap; }} .entries-table .event {{ width: 21%; }}
.entries-table .position {{ width: 27%; white-space: nowrap; }} .entries-table .description {{ width: 40%; }}
.compact-section {{ break-inside: avoid; }}
.empty {{ text-align: center; color: #64727b; }}
.report-footer {{ margin-top: 3mm; padding-top: 1.5mm; border-top: 0.2mm solid #cbd3d7; color: #5f6c74; font-size: 7pt; display: flex; justify-content: space-between; }}
@media screen and (max-width: 760px) {{
  html {{ background: #fff; }} .report {{ width: 100%; max-width: none; margin: 0; padding: 10px; }}
  .count-strip {{ grid-template-columns: repeat(2, 1fr); }}
}}
@media print {{
  html, body {{ background: #fff; }} .report {{ width: 194mm; max-width: 194mm; margin: 0; }}
  .map-frame, .compact-section, tr {{ break-inside: avoid; }}
}}
</style>
</head>
<body>
<main class="report">
<header><h1>{_escape(report_title)}</h1><div class="future-vessel-data" aria-hidden="true"></div></header>
<section aria-label="Tagesstatistik">{_statistics_table(model["statistics"])}{_count_strip(model)}</section>
{map_section}
<section><h2>Logbucheinträge</h2>
<table class="detail-table entries-table"><thead><tr><th>Zeit</th><th>Ereignis</th><th>Position</th><th>Bemerkung</th></tr></thead>
<tbody>{_event_rows(model.get("events") or [])}</tbody></table></section>
{anchor_section}
<footer class="report-footer"><span>AVNav Logbuch</span><span>{_escape(date_dash)}</span></footer>
</main>
</body>
</html>'''
