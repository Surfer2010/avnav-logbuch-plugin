#!/usr/bin/env python3

import unittest
from datetime import datetime, timezone

from exportlib.navigation_analysis import analyze_day, build_state_timeline


def event(timestamp, event_type, state):
    return {
        "timestamp": timestamp,
        "_timestamp": datetime.fromisoformat(timestamp.replace("Z", "+00:00")),
        "event_type": event_type,
        "state": state,
        "lat": 54.0,
        "lon": 10.0,
    }


class StateTimelineTests(unittest.TestCase):
    def test_first_start_event_uses_pre_event_state(self):
        events = [
            event("2026-06-01T10:00:00Z", "motor_on", {"motor": True, "sail": False, "anchor": False}),
            event("2026-06-01T10:20:00Z", "motor_off", {"motor": False, "sail": False, "anchor": False}),
        ]
        timeline, _anchors, _notes, warnings = build_state_timeline(events)
        self.assertEqual([], warnings)
        self.assertFalse(timeline[0]["before"]["motor"])
        self.assertTrue(timeline[0]["after"]["motor"])

    def test_first_end_event_infers_active_pre_event_state(self):
        events = [
            event("2026-06-01T10:20:00Z", "motor_off", {"motor": False, "sail": False, "anchor": False}),
        ]
        timeline, _anchors, _notes, warnings = build_state_timeline(events)
        self.assertEqual([], warnings)
        self.assertTrue(timeline[0]["before"]["motor"])
        self.assertFalse(timeline[0]["after"]["motor"])

    def test_duplicate_start_still_warns(self):
        events = [
            event("2026-06-01T10:00:00Z", "motor_on", {"motor": True, "sail": False, "anchor": False}),
            event("2026-06-01T10:05:00Z", "motor_on", {"motor": True, "sail": False, "anchor": False}),
        ]
        _timeline, _anchors, _notes, warnings = build_state_timeline(events)
        self.assertEqual(1, len(warnings))
        self.assertIn("already active", warnings[0])


if __name__ == "__main__":
    unittest.main()
