#!/usr/bin/env python3

from collections import OrderedDict

from exportlib.event_types import get_event_icon, get_event_label
from exportlib.local_time import to_local


def build_position(event):
    lat = event.get("lat")
    lon = event.get("lon")

    if lat is None or lon is None:
        return {
            "available": False,
            "lat": None,
            "lon": None,
            "label": "Position nicht verfügbar",
            "url": None,
            "source": event.get("position_source", "unknown"),
        }

    try:
        lat_value = float(lat)
        lon_value = float(lon)
    except Exception:
        return {
            "available": False,
            "lat": None,
            "lon": None,
            "label": "Position nicht verfügbar",
            "url": None,
            "source": event.get("position_source", "unknown"),
        }

    return {
        "available": True,
        "lat": lat_value,
        "lon": lon_value,
        "label": f"{lat_value:.5f}, {lon_value:.5f}",
        "url": (
            "https://www.openstreetmap.org/"
            f"?mlat={lat_value:.6f}&mlon={lon_value:.6f}"
            f"#map=15/{lat_value:.6f}/{lon_value:.6f}"
        ),
        "source": event.get("position_source", "unknown"),
    }


def build_entry(event):
    timestamp = event.get("_timestamp")

    if timestamp is not None:
        local_timestamp = to_local(timestamp)
        date_key = local_timestamp.strftime("%Y-%m-%d")
        date_label = local_timestamp.strftime("%d.%m.%Y")
        time_label = local_timestamp.strftime("%H:%M")
    else:
        date_key = "unknown"
        date_label = "Datum unbekannt"
        time_label = "--:--"

    event_type = event.get("event_type", "manual")

    return {
        "id": event.get("id"),
        "date_key": date_key,
        "date_label": date_label,
        "time_label": time_label,
        "event_type": event_type,
        "label": get_event_label(event_type),
        "icon": get_event_icon(event_type),
        "text": str(event.get("text") or "").strip(),
        "details": dict(event.get("details") or {}),
        "position": build_position(event),
        "source": event.get("source", "unknown"),
    }


def build_document(events, title="Digitales Logbuch"):
    days = OrderedDict()

    for event in events:
        entry = build_entry(event)
        date_key = entry["date_key"]

        if date_key not in days:
            days[date_key] = {
                "date_key": date_key,
                "date_label": entry["date_label"],
                "entries": [],
            }

        days[date_key]["entries"].append(entry)

    return {
        "title": title,
        "days": list(days.values()),
        "event_count": sum(len(day["entries"]) for day in days.values()),
    }
