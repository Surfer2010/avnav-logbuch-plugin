#!/usr/bin/env python3

from datetime import datetime
from pathlib import Path

from exportlib.navigation_analysis import analyze_day
from exportlib.read_events import find_logbuch_file, read_logbuch_file
from exportlib.read_tracks import read_gpx_points


def normalize_date(value):
    value = (value or "").strip()
    if not value:
        dt = datetime.utcnow()
    elif len(value) == 8 and value.isdigit():
        dt = datetime.strptime(value, "%Y%m%d")
    else:
        dt = datetime.strptime(value, "%Y-%m-%d")
    return dt


def load_day(logbuch_dir, tracks_dir, date_value):
    day = date_value if isinstance(date_value, datetime) else normalize_date(str(date_value))
    logbuch_dir = Path(logbuch_dir)
    logbuch_file = find_logbuch_file(logbuch_dir, day)
    if logbuch_file is None and logbuch_dir.name == "logbuch":
        logbuch_file = find_logbuch_file(logbuch_dir.with_name("logbuch"), day)
    if logbuch_file is None:
        raise FileNotFoundError(f"No logbuch file found for {day:%Y-%m-%d}")
    gpx_file = Path(tracks_dir) / f"{day:%Y-%m-%d}.gpx"
    events = read_logbuch_file(logbuch_file)
    track_points, track_warnings = read_gpx_points(gpx_file)
    model = analyze_day(events, track_points)
    model.update({
        "date": day,
        "date_dash": day.strftime("%Y-%m-%d"),
        "date_compact": day.strftime("%Y%m%d"),
        "logbuch_file": logbuch_file,
        "gpx_file": gpx_file,
    })
    model["warnings"] = track_warnings + model["warnings"]
    return model


def combine_statistics(models):
    result = {
        key: {"distance_nm": 0.0, "duration_seconds": 0.0, "max_speed_kn": 0.0, "segment_count": 0}
        for key in ("sail", "motor", "unknown", "total")
    }
    counts = {"events": 0, "anchorages": 0, "notes": 0, "invalid_segments": 0}
    for model in models:
        stats = model["statistics"]
        for key in result:
            result[key]["distance_nm"] += stats[key]["distance_nm"]
            result[key]["duration_seconds"] += stats[key]["duration_seconds"]
            result[key]["max_speed_kn"] = max(result[key]["max_speed_kn"], stats[key]["max_speed_kn"])
            result[key]["segment_count"] += stats[key]["segment_count"]
        for key in counts:
            counts[key] += stats["counts"].get(key, 0)
    for bucket in result.values():
        hours = bucket["duration_seconds"] / 3600.0
        bucket["average_speed_kn"] = bucket["distance_nm"] / hours if hours > 0 else 0.0
    result["counts"] = counts
    return result
