#!/usr/bin/env python3

import html


POSITION_SOURCE_LABELS = {
    "live": "Live-Position",
    "track_exact": "Exakter Trackpunkt",
    "interpolated": "Aus Trackdaten interpoliert",
    "manual": "Manuell eingetragen",
    "unknown": "Unbekannte Positionsquelle",
}


def escape(value):
    return html.escape(str(value), quote=True)


def format_detail_key(key):
    labels = {
        "engine_hours": "Motorstunden",
        "rpm": "Drehzahl",
        "mainsail": "Großsegel",
        "headsail": "Vorsegel",
        "reef": "Reff",
        "tws": "Wahre Windgeschwindigkeit",
        "twd": "Wahre Windrichtung",
        "pressure": "Luftdruck",
        "temperature": "Temperatur",
        "depth": "Wassertiefe",
        "mooring_type": "Liegeart",
        "place_name": "Ort",
        "created_later": "Nachträglich erfasst",
        "recorded_at": "Erfasst am",
    }

    return labels.get(key, key.replace("_", " ").capitalize())


def format_detail_value(value):
    if isinstance(value, bool):
        return "Ja" if value else "Nein"

    if value is None:
        return ""

    return str(value)


def render_entry(entry):
    position = entry["position"]
    parts = [
        '<article class="log-entry">',
        '<div class="entry-header">',
        f'<span class="entry-time">{escape(entry["time_label"])}</span>',
        f'<h3>{escape(entry["label"])}</h3>',
        "</div>",
    ]

    if position["available"]:
        parts.extend([
            '<p class="position">',
            "<strong>Position:</strong> ",
            (
                f'<a href="{escape(position["url"])}" '
                'target="_blank" rel="noopener noreferrer">'
                f'{escape(position["label"])}</a>'
            ),
            "</p>",
        ])

        source = position.get("source", "unknown")

        if source not in ("live", "unknown"):
            source_label = POSITION_SOURCE_LABELS.get(source, source)
            parts.append(
                f'<p class="position-source">{escape(source_label)}</p>'
            )
    else:
        parts.append(
            '<p class="position"><strong>Position:</strong> '
            "Position nicht verfügbar</p>"
        )

    if entry.get("text"):
        parts.append(
            f'<p class="entry-text">{escape(entry["text"])}</p>'
        )

    details = entry.get("details") or {}

    if details:
        detail_items = []

        for key, value in details.items():
            formatted_value = format_detail_value(value)

            if formatted_value == "":
                continue

            detail_items.append(
                "<li>"
                f"<strong>{escape(format_detail_key(key))}:</strong> "
                f"{escape(formatted_value)}"
                "</li>"
            )

        if detail_items:
            parts.extend([
                '<div class="details">',
                "<strong>Zusatzdaten:</strong>",
                "<ul>",
                "".join(detail_items),
                "</ul>",
                "</div>",
            ])

    parts.append("</article>")

    return "".join(parts)


def render_html(document):
    day_sections = []

    for day in document["days"]:
        entries = "".join(
            render_entry(entry)
            for entry in day["entries"]
        )

        day_sections.append(
            '<section class="log-day">'
            f'<h2>{escape(day["date_label"])}</h2>'
            f"{entries}"
            "</section>"
        )

    if not day_sections:
        day_sections.append(
            '<p class="empty">Keine Logbucheinträge im gewählten Zeitraum.</p>'
        )

    return f"""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(document["title"])}</title>
<style>
:root {{
    color-scheme: light dark;
    font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}}

body {{
    margin: 0;
    background: #f4f6f8;
    color: #1f2933;
}}

main {{
    max-width: 920px;
    margin: 0 auto;
    padding: 1rem;
}}

h1 {{
    margin: 0 0 1.5rem;
}}

.log-day {{
    margin-bottom: 2rem;
}}

.log-day > h2 {{
    position: sticky;
    top: 0;
    margin: 0 0 1rem;
    padding: 0.75rem 0;
    background: #f4f6f8;
    border-bottom: 2px solid #9aa5b1;
}}

.log-entry {{
    margin-bottom: 1rem;
    padding: 1rem;
    background: #ffffff;
    border: 1px solid #d9e2ec;
    border-radius: 0.5rem;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
}}

.entry-header {{
    display: flex;
    align-items: baseline;
    gap: 0.75rem;
    margin-bottom: 0.75rem;
}}

.entry-header h3 {{
    margin: 0;
    font-size: 1.1rem;
}}

.entry-time {{
    font-weight: 700;
    white-space: nowrap;
}}

.position,
.entry-text,
.position-source {{
    margin: 0.5rem 0;
}}

.position-source {{
    font-size: 0.9rem;
    font-style: italic;
    color: #52606d;
}}

.details ul {{
    margin-bottom: 0;
}}

a {{
    color: #005ea8;
}}

.empty {{
    padding: 1rem;
    background: #ffffff;
    border-radius: 0.5rem;
}}

@media (max-width: 600px) {{
    main {{
        padding: 0.75rem;
    }}

    .entry-header {{
        display: block;
    }}

    .entry-time {{
        display: block;
        margin-bottom: 0.25rem;
    }}
}}

@media (prefers-color-scheme: dark) {{
    body,
    .log-day > h2 {{
        background: #111827;
        color: #f9fafb;
    }}

    .log-entry,
    .empty {{
        background: #1f2937;
        border-color: #4b5563;
    }}

    .position-source {{
        color: #cbd5e1;
    }}

    a {{
        color: #7dd3fc;
    }}
}}

@media print {{
    body {{
        background: #ffffff;
        color: #000000;
    }}

    main {{
        max-width: none;
    }}

    .log-day > h2 {{
        position: static;
        background: transparent;
    }}

    .log-entry {{
        box-shadow: none;
        break-inside: avoid;
    }}
}}
</style>
</head>
<body>
<main>
<h1>{escape(document["title"])}</h1>
{''.join(day_sections)}
</main>
</body>
</html>
"""
