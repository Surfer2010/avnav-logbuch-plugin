#!/usr/bin/env python3

import math
from collections import defaultdict

START_EVENTS = {"motor_on": "motor", "sail_set": "sail", "anchor_down": "anchor"}
END_EVENTS = {"motor_off": "motor", "sail_down": "sail", "anchor_up": "anchor"}
NOTE_EVENTS = {"manual", "trip_start", "trip_end"}
EARTH_RADIUS_M = 6371000.0
MPS_TO_KNOTS = 1.9438444924406


def haversine_meters(lat1, lon1, lat2, lon2):
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return EARTH_RADIUS_M * 2 * math.atan2(math.sqrt(a), math.sqrt(max(0.0, 1 - a)))


def build_state_timeline(events):
    events = [event for event in events if event.get("_timestamp") is not None]
    events.sort(key=lambda event: event["_timestamp"])
    state = {"motor": False, "sail": False, "anchor": False}
    timeline = []
    anchors = []
    notes = []
    warnings = []

    if events:
        stored = events[0].get("state") or {}
        for key in state:
            if isinstance(stored.get(key), bool):
                state[key] = stored[key]

    for event in events:
        event_type = event.get("event_type")
        if event_type in NOTE_EVENTS:
            notes.append(event)

        before = dict(state)
        if event_type in START_EVENTS:
            key = START_EVENTS[event_type]
            if state[key]:
                warnings.append(f"WARNING: {key} already active at {event.get('timestamp')}")
            state[key] = True
            if key == "anchor":
                anchors.append(event)
        elif event_type in END_EVENTS:
            key = END_EVENTS[event_type]
            if not state[key]:
                warnings.append(f"WARNING: {key} already inactive at {event.get('timestamp')}")
            state[key] = False

        timeline.append({"timestamp": event["_timestamp"], "before": before, "after": dict(state), "event": event})

    return timeline, anchors, notes, warnings


def state_at(timestamp, timeline):
    state = {"motor": False, "sail": False, "anchor": False}
    for change in timeline:
        if change["timestamp"] > timestamp:
            break
        state = change["after"]
    return state


def classify_state(state):
    if state.get("motor"):
        return "motor"
    if state.get("sail"):
        return "sail"
    return "unknown"


def build_track_segments(points, timeline, max_gap_seconds=900, max_speed_kn=60.0):
    segments = []
    warnings = []
    for index in range(1, len(points)):
        start = points[index - 1]
        end = points[index]
        duration = (end["timestamp"] - start["timestamp"]).total_seconds()
        if duration <= 0:
            warnings.append(f"WARNING: non-positive track duration at {end['time']}")
            continue
        distance_m = haversine_meters(start["lat"], start["lon"], end["lat"], end["lon"])
        derived_speed_kn = (distance_m / duration) * MPS_TO_KNOTS
        measured = end.get("speed_mps")
        speed_kn = measured * MPS_TO_KNOTS if measured is not None else derived_speed_kn
        valid = duration <= max_gap_seconds and speed_kn <= max_speed_kn
        category = classify_state(state_at(start["timestamp"], timeline)) if valid else "invalid"
        segments.append({
            "start": start,
            "end": end,
            "start_time": start["timestamp"],
            "end_time": end["timestamp"],
            "duration_seconds": duration,
            "distance_m": distance_m,
            "distance_nm": distance_m / 1852.0,
            "speed_kn": speed_kn,
            "derived_speed_kn": derived_speed_kn,
            "category": category,
            "valid": valid,
        })
        if not valid:
            warnings.append(f"WARNING: rejected track segment at {end['time']} gap={duration:.0f}s speed={speed_kn:.1f}kn")
    return segments, warnings


def group_segments(segments):
    groups = []
    current = None
    for segment in segments:
        if not segment["valid"]:
            continue
        key = segment["category"]
        if current is None or current["category"] != key or current["segments"][-1]["end_time"] != segment["start_time"]:
            current = {"category": key, "segments": []}
            groups.append(current)
        current["segments"].append(segment)

    for group in groups:
        items = group["segments"]
        group["points"] = [items[0]["start"]] + [item["end"] for item in items]
        group["start_time"] = items[0]["start_time"]
        group["end_time"] = items[-1]["end_time"]
        group["duration_seconds"] = sum(item["duration_seconds"] for item in items)
        group["distance_nm"] = sum(item["distance_nm"] for item in items)
        group["max_speed_kn"] = max((item["speed_kn"] for item in items), default=0.0)
        group["average_speed_kn"] = group["distance_nm"] / (group["duration_seconds"] / 3600.0) if group["duration_seconds"] > 0 else 0.0
    return groups


def build_statistics(segments, anchors, notes, event_count):
    buckets = defaultdict(lambda: {"distance_nm": 0.0, "duration_seconds": 0.0, "max_speed_kn": 0.0, "segment_count": 0})
    for segment in segments:
        if not segment["valid"]:
            continue
        category = segment["category"]
        bucket = buckets[category]
        bucket["distance_nm"] += segment["distance_nm"]
        bucket["duration_seconds"] += segment["duration_seconds"]
        bucket["max_speed_kn"] = max(bucket["max_speed_kn"], segment["speed_kn"])
        bucket["segment_count"] += 1

    def finalize(bucket):
        result = dict(bucket)
        hours = result["duration_seconds"] / 3600.0
        result["average_speed_kn"] = result["distance_nm"] / hours if hours > 0 else 0.0
        return result

    sail = finalize(buckets["sail"])
    motor = finalize(buckets["motor"])
    unknown = finalize(buckets["unknown"])
    valid_segments = [segment for segment in segments if segment["valid"]]
    total = finalize({
        "distance_nm": sum(segment["distance_nm"] for segment in valid_segments),
        "duration_seconds": sum(segment["duration_seconds"] for segment in valid_segments),
        "max_speed_kn": max((segment["speed_kn"] for segment in valid_segments), default=0.0),
        "segment_count": len(valid_segments),
    })
    return {
        "sail": sail,
        "motor": motor,
        "unknown": unknown,
        "total": total,
        "counts": {
            "events": event_count,
            "anchorages": len(anchors),
            "notes": len(notes),
            "invalid_segments": sum(1 for segment in segments if not segment["valid"]),
        },
    }


def analyze_day(events, track_points):
    timeline, anchors, notes, warnings = build_state_timeline(events)
    segments, segment_warnings = build_track_segments(track_points, timeline)
    groups = group_segments(segments)
    statistics = build_statistics(segments, anchors, notes, len(events))
    positioned_notes = [event for event in notes if event.get("lat") is not None and event.get("lon") is not None]
    positioned_anchors = [event for event in anchors if event.get("lat") is not None and event.get("lon") is not None]
    bounds = None
    if track_points:
        bounds = {
            "min_lat": min(point["lat"] for point in track_points),
            "max_lat": max(point["lat"] for point in track_points),
            "min_lon": min(point["lon"] for point in track_points),
            "max_lon": max(point["lon"] for point in track_points),
        }
    return {
        "events": events,
        "track_points": track_points,
        "timeline": timeline,
        "segments": segments,
        "segment_groups": groups,
        "anchors": positioned_anchors,
        "notes": positioned_notes,
        "statistics": statistics,
        "bounds": bounds,
        "warnings": warnings + segment_warnings,
    }
