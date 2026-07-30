#!/usr/bin/env python3

from datetime import datetime, timedelta, timezone
from pathlib import Path

from exportlib.navigation_analysis import analyze_day
from exportlib.read_events import find_logbuch_file, read_logbuch_file
from exportlib.read_tracks import read_gpx_points


def parse_range_datetime(value, end=False):
    value = str(value or "").strip()

    if not value:
        raise ValueError("Zeitangabe fehlt")

    if value.endswith("Z"):
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    else:
        parsed = datetime.fromisoformat(value)

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)

    parsed = parsed.astimezone(timezone.utc)

    if end:
        parsed = parsed.replace(second=59, microsecond=999999)
    else:
        parsed = parsed.replace(second=0, microsecond=0)

    return parsed


def _day_range(start, end):
    current = start.date()

    while current <= end.date():
        yield current
        current += timedelta(days=1)


def _in_range(timestamp, start, end):
    if timestamp is None:
        return False

    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)
    else:
        timestamp = timestamp.astimezone(timezone.utc)

    return start <= timestamp <= end


def _has_position(entry):
    return (
        entry.get("lat") is not None
        and entry.get("lon") is not None
    )


def load_range(
    logbuch_dir,
    tracks_dir,
    from_value,
    to_value,
    *,
    include_without_position=True,
):
    start = parse_range_datetime(from_value, end=False)
    end = parse_range_datetime(to_value, end=True)

    if start > end:
        raise ValueError("Von darf nicht nach Bis liegen")

    logbuch_dir = Path(logbuch_dir)
    tracks_dir = Path(tracks_dir)

    all_events = []
    all_track_points = []
    warnings = []
    source_files = []

    for day_value in _day_range(start, end):
        day_datetime = datetime(
            day_value.year,
            day_value.month,
            day_value.day,
        )

        logbuch_file = find_logbuch_file(logbuch_dir, day_datetime)

        if logbuch_file is not None:
            source_files.append(str(logbuch_file))

            for event in read_logbuch_file(logbuch_file):
                timestamp = event.get("_timestamp")

                if not _in_range(timestamp, start, end):
                    continue

                if not include_without_position and not _has_position(event):
                    continue

                all_events.append(event)

        gpx_file = tracks_dir / f"{day_value:%Y-%m-%d}.gpx"

        if not gpx_file.exists():
            warnings.append(f"GPX file not found: {gpx_file}")
            continue

        try:
            points, track_warnings = read_gpx_points(gpx_file)
        except Exception as error:
            warnings.append(str(error))
            continue

        all_track_points.extend(
            point
            for point in points
            if _in_range(point.get("timestamp"), start, end)
        )
        warnings.extend(track_warnings)

    all_events.sort(
        key=lambda item: (
            item.get("_timestamp") is None,
            item.get("_timestamp"),
        )
    )
    all_track_points.sort(key=lambda item: item["timestamp"])

    model = analyze_day(all_events, all_track_points)

    model.update({
        "range_start": start,
        "range_end": end,
        "range_start_iso": start.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "range_end_iso": end.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "range_start_label": start.strftime("%d.%m.%Y %H:%M"),
        "range_end_label": end.strftime("%d.%m.%Y %H:%M"),
        "date_dash": (
            start.strftime("%Y-%m-%d")
            if start.date() == end.date()
            else (
                start.strftime("%Y-%m-%d")
                + "_bis_"
                + end.strftime("%Y-%m-%d")
            )
        ),
        "date_compact": (
            start.strftime("%Y%m%d-%H%M")
            + "_bis_"
            + end.strftime("%Y%m%d-%H%M")
        ),
        "source_files": source_files,
        "include_without_position": include_without_position,
    })

    model["warnings"] = warnings + model.get("warnings", [])

    return model
