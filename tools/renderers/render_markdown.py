#!/usr/bin/env python3

POSITION_SOURCE_LABELS = {
    "live": "Live-Position",
    "track_exact": "Exakter Trackpunkt",
    "interpolated": "Aus Trackdaten interpoliert",
    "manual": "Manuell eingetragen",
    "unknown": "Unbekannte Positionsquelle",
}


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
    lines = [
        f"### {entry['time_label']} – {entry['label']}",
        "",
    ]

    position = entry["position"]

    if position["available"]:
        lines.append(
            f"**Position:** [{position['label']}]({position['url']})"
        )

        source = position.get("source", "unknown")

        if source not in ("live", "unknown"):
            source_label = POSITION_SOURCE_LABELS.get(source, source)
            lines.extend(["", f"*{source_label}.*"])
    else:
        lines.append("**Position:** Position nicht verfügbar")

    if entry.get("text"):
        lines.extend(["", entry["text"]])

    details = entry.get("details") or {}

    if details:
        lines.extend(["", "**Zusatzdaten:**", ""])

        for key, value in details.items():
            formatted_value = format_detail_value(value)

            if formatted_value != "":
                lines.append(
                    f"- **{format_detail_key(key)}:** {formatted_value}"
                )

    lines.extend(["", "---", ""])

    return lines


def render_markdown(document):
    lines = [
        f"# {document['title']}",
        "",
    ]

    if not document["days"]:
        lines.extend([
            "Keine Logbucheinträge im gewählten Zeitraum.",
            "",
        ])

        return "\n".join(lines)

    for day in document["days"]:
        lines.extend([
            f"## {day['date_label']}",
            "",
        ])

        for entry in day["entries"]:
            lines.extend(render_entry(entry))

    return "\n".join(lines).rstrip() + "\n"
