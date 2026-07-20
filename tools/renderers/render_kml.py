#!/usr/bin/env python3

import zipfile
from pathlib import Path

from exportlib.formatting import escape, format_hms

CATEGORY_LABELS = {"motor": "Motor", "sail": "Segel", "unknown": "Unbekannt"}
STYLE_IDS = {"motor": "motorLine", "sail": "sailLine", "unknown": "unknownLine"}


def _coordinates(points):
    return "\n".join(f"          {p['lon']:.9f},{p['lat']:.9f},0" for p in points)


def _stats_table(stats):
    rows = []
    for key, label in (("sail", "Segel"), ("motor", "Motor"), ("unknown", "Unbekannt"), ("total", "Gesamt")):
        item = stats[key]
        rows.append(
            "<tr>"
            f"<td><b>{escape(label)}</b></td>"
            f"<td>{item['distance_nm']:.2f} sm</td>"
            f"<td>{format_hms(item['duration_seconds'])}</td>"
            f"<td>{item['max_speed_kn']:.2f} kn</td>"
            f"<td>{item['average_speed_kn']:.2f} kn</td>"
            "</tr>"
        )
    counts = stats["counts"]
    return (
        '<table border="1" cellpadding="4" cellspacing="0">'
        '<tr><th></th><th>Strecke</th><th>Zeit</th><th>Maximum</th><th>Durchschnitt</th></tr>'
        + "".join(rows)
        + f"<tr><td><b>Logbucheinträge</b></td><td colspan=4>{counts['events']}</td></tr>"
        + f"<tr><td><b>Ankerplätze</b></td><td colspan=4>{counts['anchorages']}</td></tr>"
        + f"<tr><td><b>Logbuchnotizen</b></td><td colspan=4>{counts['notes']}</td></tr>"
        + "</table>"
    )


def _line_placemark(name, group):
    category = group["category"]
    description = (
        f"<h2>{escape(CATEGORY_LABELS.get(category, category))}</h2>"
        '<table border="1" cellpadding="4" cellspacing="0">'
        f"<tr><td><b>Start</b></td><td>{escape(group['start_time'].isoformat())}</td></tr>"
        f"<tr><td><b>Ende</b></td><td>{escape(group['end_time'].isoformat())}</td></tr>"
        f"<tr><td><b>Dauer</b></td><td>{format_hms(group['duration_seconds'])}</td></tr>"
        f"<tr><td><b>Distanz</b></td><td>{group['distance_nm']:.2f} sm</td></tr>"
        f"<tr><td><b>Maximum</b></td><td>{group['max_speed_kn']:.2f} kn</td></tr>"
        f"<tr><td><b>Durchschnitt</b></td><td>{group['average_speed_kn']:.2f} kn</td></tr>"
        "</table>"
    )
    return f"""
    <Placemark>
      <name>{escape(name)}</name>
      <description><![CDATA[{description}]]></description>
      <styleUrl>#{STYLE_IDS.get(category, 'unknownLine')}</styleUrl>
      <TimeSpan><begin>{escape(group['start_time'].isoformat())}</begin><end>{escape(group['end_time'].isoformat())}</end></TimeSpan>
      <LineString><tessellate>1</tessellate><coordinates>
{_coordinates(group['points'])}
      </coordinates></LineString>
    </Placemark>
"""


def _point_placemark(name, entry, style_id):
    text = entry.get("text") or ""
    return f"""
    <Placemark>
      <name>{escape(name)}</name>
      <description><![CDATA[
        <h2>{escape(name)}</h2>
        <p><b>Zeit:</b> {escape(entry.get('timestamp'))}</p>
        <p><b>Position:</b> {escape(entry.get('lat'))}, {escape(entry.get('lon'))}</p>
        {f'<p>{escape(text)}</p>' if text else ''}
      ]]></description>
      <styleUrl>#{style_id}</styleUrl>
      <TimeStamp><when>{escape(entry.get('timestamp'))}</when></TimeStamp>
      <Point><coordinates>{float(entry['lon']):.9f},{float(entry['lat']):.9f},0</coordinates></Point>
    </Placemark>
"""


def render_day_folder(model, prefix_names=False):
    date_dash = model["date_dash"]
    folders = {"motor": [], "sail": [], "unknown": []}
    counters = {"motor": 0, "sail": 0, "unknown": 0}
    for group in model["segment_groups"]:
        category = group["category"]
        counters[category] += 1
        label = CATEGORY_LABELS.get(category, category)
        name = f"{date_dash} {label} {counters[category]}" if prefix_names else f"{label} {counters[category]}"
        folders[category].append(_line_placemark(name, group))

    anchors = [_point_placemark(f"{date_dash + ' ' if prefix_names else ''}Anker {i}", entry, "anchorPoint") for i, entry in enumerate(model["anchors"], 1)]
    notes = []
    for i, entry in enumerate(model["notes"], 1):
        event_type = entry.get("event_type")
        title = "Törn Start" if event_type == "trip_start" else "Törn Ende" if event_type == "trip_end" else f"Logbuchnotiz {i}"
        if prefix_names:
            title = f"{date_dash} {title}"
        notes.append(_point_placemark(title, entry, "notePoint"))

    return f"""
  <Folder>
    <name>{escape(date_dash)}</name>
    <description><![CDATA[<h1>Logbuch {escape(date_dash)}</h1>{_stats_table(model['statistics'])}]]></description>
    <Folder><name>Motorstrecken</name>{''.join(folders['motor'])}</Folder>
    <Folder><name>Segelstrecken</name>{''.join(folders['sail'])}</Folder>
    <Folder><name>Unbekannte Strecken</name>{''.join(folders['unknown'])}</Folder>
    <Folder><name>Ankerpunkte</name>{''.join(anchors)}</Folder>
    <Folder><name>Logbuchnotizen</name>{''.join(notes)}</Folder>
  </Folder>
"""


def _styles():
    return """
  <Style id="motorLine"><LineStyle><color>ff0000ff</color><width>4</width></LineStyle></Style>
  <Style id="sailLine"><LineStyle><color>ff00aa00</color><width>4</width></LineStyle></Style>
  <Style id="unknownLine"><LineStyle><color>ff888888</color><width>3</width></LineStyle></Style>
  <Style id="anchorPoint"><IconStyle><scale>1.2</scale><Icon><href>icons/anchor.png</href></Icon></IconStyle></Style>
  <Style id="notePoint"><IconStyle><scale>1.0</scale><Icon><href>icons/note.png</href></Icon></IconStyle></Style>
"""


def render_day_kml(model):
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2"><Document>
  <name>Logbuch {escape(model['date_dash'])}</name>
  <description><![CDATA[<h1>Logbuch {escape(model['date_dash'])}</h1>{_stats_table(model['statistics'])}]]></description>
{_styles()}
{render_day_folder(model)}
</Document></kml>'''


def render_trip_kml(start_dash, end_dash, models, total_stats):
    folders = "".join(render_day_folder(model, prefix_names=True) for model in models)
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2"><Document>
  <name>Törnlogbuch {escape(start_dash)} bis {escape(end_dash)}</name>
  <description><![CDATA[<h1>Törnlogbuch {escape(start_dash)} bis {escape(end_dash)}</h1>{_stats_table(total_stats)}]]></description>
{_styles()}
{folders}
</Document></kml>'''


def write_kmz(output_file, kml_content, icons_dir):
    output_file = Path(output_file)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    tmp_file = output_file.with_name(output_file.name + ".tmp")
    if tmp_file.exists():
        tmp_file.unlink()
    try:
        with zipfile.ZipFile(tmp_file, "w", zipfile.ZIP_DEFLATED) as kmz:
            kmz.writestr("doc.kml", kml_content)
            for name in ("anchor.png", "note.png"):
                icon = Path(icons_dir) / name
                if icon.exists():
                    kmz.write(icon, f"icons/{name}")
        tmp_file.replace(output_file)
    finally:
        if tmp_file.exists():
            tmp_file.unlink()
