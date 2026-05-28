#!/usr/bin/env python3
"""
Analyze AVNav Logbuch JSONL files.

This script reads one or more JSONL logbuch files and calculates:
- motor runtime
- sailing time
- anchor time
- number of logbuch entries
- open intervals

The script currently works event-based:
- motor_on    -> motor_off
- sail_set    -> sail_down
- anchor_down -> anchor_up
"""

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


START_EVENTS = {
    "motor_on": "motor",
    "sail_set": "sail",
    "anchor_down": "anchor",
}

END_EVENTS = {
    "motor_off": "motor",
    "sail_down": "sail",
    "anchor_up": "anchor",
}


def parse_timestamp(value):
    """Parse ISO timestamp with trailing Z."""
    if not value:
        return None

    value = value.replace("Z", "+00:00")

    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def read_entries(paths):
    """Read JSONL entries from all given files."""
    entries = []

    for path in paths:
        path = Path(path)

        if not path.exists():
            continue

        with path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                line = line.strip()

                if not line:
                    continue

                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    print(f"WARNING: invalid JSON in {path}:{line_number}")
                    continue

                timestamp = parse_timestamp(entry.get("timestamp"))

                if timestamp is None:
                    print(f"WARNING: invalid timestamp in {path}:{line_number}")
                    continue

                entry["_timestamp"] = timestamp
                entry["_file"] = str(path)
                entries.append(entry)

    entries.sort(key=lambda item: item["_timestamp"])
    return entries


def seconds_to_hms(seconds):
    """Format seconds as HH:MM:SS."""
    seconds = int(seconds)
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60

    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def analyze(entries):
    """Analyze entries and calculate durations."""
    totals = {
        "motor": 0,
        "sail": 0,
        "anchor": 0,
    }

    open_states = {
        "motor": None,
        "sail": None,
        "anchor": None,
    }

    intervals = []

    for entry in entries:
        event_type = entry.get("event_type")
        timestamp = entry["_timestamp"]

        if event_type in START_EVENTS:
            state_name = START_EVENTS[event_type]

            if open_states[state_name] is None:
                open_states[state_name] = entry
            else:
                intervals.append({
                    "type": state_name,
                    "status": "warning_already_open",
                    "start": open_states[state_name]["timestamp"],
                    "event": entry.get("timestamp"),
                })

        elif event_type in END_EVENTS:
            state_name = END_EVENTS[event_type]
            start_entry = open_states[state_name]

            if start_entry is None:
                intervals.append({
                    "type": state_name,
                    "status": "warning_end_without_start",
                    "end": entry.get("timestamp"),
                })
                continue

            duration = (timestamp - start_entry["_timestamp"]).total_seconds()

            if duration < 0:
                duration = 0

            totals[state_name] += duration

            intervals.append({
                "type": state_name,
                "status": "closed",
                "start": start_entry.get("timestamp"),
                "end": entry.get("timestamp"),
                "duration_seconds": duration,
                "duration": seconds_to_hms(duration),
                "start_lat": start_entry.get("lat"),
                "start_lon": start_entry.get("lon"),
                "end_lat": entry.get("lat"),
                "end_lon": entry.get("lon"),
            })

            open_states[state_name] = None

    open_intervals = {}

    for state_name, start_entry in open_states.items():
        if start_entry is not None:
            open_intervals[state_name] = {
                "start": start_entry.get("timestamp"),
                "lat": start_entry.get("lat"),
                "lon": start_entry.get("lon"),
            }

    return {
        "entry_count": len(entries),
        "totals_seconds": totals,
        "totals": {
            "motor": seconds_to_hms(totals["motor"]),
            "sail": seconds_to_hms(totals["sail"]),
            "anchor": seconds_to_hms(totals["anchor"]),
        },
        "open_intervals": open_intervals,
        "intervals": intervals,
    }


def write_markdown(result, output_path):
    """Write a simple Markdown report."""
    lines = []

    lines.append("# AVNav Logbuch Auswertung")
    lines.append("")
    lines.append("## Zusammenfassung")
    lines.append("")
    lines.append(f"- Einträge: {result['entry_count']}")
    lines.append(f"- Motorzeit: {result['totals']['motor']}")
    lines.append(f"- Segelzeit: {result['totals']['sail']}")
    lines.append(f"- Ankerzeit: {result['totals']['anchor']}")
    lines.append("")

    if result["open_intervals"]:
        lines.append("## Offene Intervalle")
        lines.append("")

        for name, data in result["open_intervals"].items():
            lines.append(f"- {name}: offen seit {data['start']}")

        lines.append("")

    lines.append("## Intervalle")
    lines.append("")
    lines.append("| Typ | Status | Start | Ende | Dauer |")
    lines.append("|---|---|---|---|---|")

    for interval in result["intervals"]:
        lines.append(
            "| {type} | {status} | {start} | {end} | {duration} |".format(
                type=interval.get("type", ""),
                status=interval.get("status", ""),
                start=interval.get("start", ""),
                end=interval.get("end", ""),
                duration=interval.get("duration", ""),
            )
        )

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Analyze AVNav Logbuch JSONL files")
    parser.add_argument("files", nargs="+", help="JSONL logbuch files")
    parser.add_argument("--json", default="exports/logbuch-analysis.json", help="JSON output path")
    parser.add_argument("--markdown", default="exports/logbuch-analysis.md", help="Markdown output path")

    args = parser.parse_args()

    entries = read_entries(args.files)
    result = analyze(entries)

    json_path = Path(args.json)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")

    write_markdown(result, args.markdown)

    print("Entries:", result["entry_count"])
    print("Motor:", result["totals"]["motor"])
    print("Sail:", result["totals"]["sail"])
    print("Anchor:", result["totals"]["anchor"])
    print("JSON:", args.json)
    print("Markdown:", args.markdown)


if __name__ == "__main__":
    main()
