#!/usr/bin/env python3

from pathlib import Path
from xml.etree import ElementTree as ET

from exportlib.formatting import parse_datetime

GPX_NS = {"gpx": "http://www.topografix.com/GPX/1/1"}


def _float_or_none(value):
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def read_gpx_points(path):
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"GPX file not found: {path}")

    root = ET.parse(path).getroot()
    points = []
    warnings = []

    for index, trkpt in enumerate(root.findall(".//gpx:trkpt", GPX_NS), start=1):
        time_node = trkpt.find("gpx:time", GPX_NS)
        if time_node is None or not time_node.text:
            warnings.append(f"GPX point {index}: missing timestamp")
            continue

        timestamp = parse_datetime(time_node.text)
        lat = _float_or_none(trkpt.attrib.get("lat"))
        lon = _float_or_none(trkpt.attrib.get("lon"))
        if timestamp is None or lat is None or lon is None:
            warnings.append(f"GPX point {index}: invalid timestamp or position")
            continue

        course_node = trkpt.find("gpx:course", GPX_NS)
        speed_node = trkpt.find("gpx:speed", GPX_NS)
        points.append({
            "timestamp": timestamp,
            "time": time_node.text,
            "lat": lat,
            "lon": lon,
            "course": _float_or_none(course_node.text if course_node is not None else None),
            "speed_mps": _float_or_none(speed_node.text if speed_node is not None else None),
        })

    points.sort(key=lambda item: item["timestamp"])
    return points, warnings
