#!/usr/bin/env python3

import json
import uuid
from datetime import datetime, timedelta
from pathlib import Path


def parse_timestamp(value):
    if not value:
        return None

    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except Exception:
        return None


def timestamp_sort_key(event):
    timestamp = event.get("_timestamp")

    if timestamp is None:
        return float("inf")

    return timestamp.timestamp()


def normalize_event(entry):
    if not isinstance(entry, dict):
        return None

    event = dict(entry)

    event.setdefault("schema_version", 0)
    event.setdefault("event_type", "manual")
    event.setdefault("text", "")
    event.setdefault("details", {})
    event.setdefault("state", {})
    event.setdefault("source", "unknown")

    if not isinstance(event.get("details"), dict):
        event["details"] = {}

    if not isinstance(event.get("state"), dict):
        event["state"] = {}

    if not event.get("position_source"):
        if event.get("lat") is not None and event.get("lon") is not None:
            event["position_source"] = "live"
        else:
            event["position_source"] = "unknown"

    if not event.get("id"):
        seed = json.dumps(
            event,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        )
        event["id"] = str(
            uuid.uuid5(uuid.NAMESPACE_URL, "avnav-logbuch:" + seed)
        )

    event["_timestamp"] = parse_timestamp(event.get("timestamp"))

    return event


def find_logbook_file(logbook_dir, date_value):
    date_dash = date_value.strftime("%Y-%m-%d")
    date_compact = date_value.strftime("%Y%m%d")

    candidates = [
        Path(logbook_dir) / f"{date_compact}_logbuch.jsonl",
        Path(logbook_dir) / f"logbuch-{date_dash}.jsonl",
    ]

    for path in candidates:
        if path.exists():
            return path

    return None


def read_logbook_file(path):
    events = []

    with Path(path).open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            line = line.strip()

            if not line:
                continue

            try:
                event = normalize_event(json.loads(line))

                if event is not None:
                    events.append(event)

            except Exception as error:
                print(
                    f"WARNING: invalid logbook line "
                    f"{path}:{line_number}: {error}"
                )

    events.sort(key=timestamp_sort_key)

    return events


def read_events(logbook_dir, start_date, end_date):
    events = []
    current = start_date

    while current <= end_date:
        path = find_logbook_file(logbook_dir, current)

        if path is not None:
            events.extend(read_logbook_file(path))

        current += timedelta(days=1)

    events.sort(key=timestamp_sort_key)

    return events
