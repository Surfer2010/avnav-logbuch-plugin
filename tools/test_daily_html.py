#!/usr/bin/env python3

import unittest
from datetime import datetime, timezone

from exportlib.navigation_analysis import analyze_day
from renderers.render_daily_html import render_daily_html


class DailyHtmlTests(unittest.TestCase):
    def _model(self):
        events = [
            {"timestamp": "2026-06-01T10:00:00Z", "_timestamp": datetime(2026, 6, 1, 10, 0, tzinfo=timezone.utc), "event_type": "motor_on", "text": "", "lat": 54.0, "lon": 10.0, "state": {"motor": True}},
            {"timestamp": "2026-06-01T10:10:00Z", "_timestamp": datetime(2026, 6, 1, 10, 10, tzinfo=timezone.utc), "event_type": "motor_off", "text": "Hafen verlassen", "lat": 54.01, "lon": 10.02, "state": {"motor": False}},
        ]
        points = [
            {"timestamp": datetime(2026, 6, 1, 10, 0, tzinfo=timezone.utc), "time": "2026-06-01T10:00:00Z", "lat": 54.0, "lon": 10.0, "speed_mps": 2.0},
            {"timestamp": datetime(2026, 6, 1, 10, 10, tzinfo=timezone.utc), "time": "2026-06-01T10:10:00Z", "lat": 54.01, "lon": 10.02, "speed_mps": 2.0},
        ]
        model = analyze_day(events, points)
        model.update({"date_dash": "2026-06-01", "date_compact": "20260601"})
        return model

    def test_report_is_self_contained_and_a4(self):
        content = render_daily_html(self._model(), online_map=False)
        self.assertIn("@page { size: A4 portrait; margin: 8mm; }", content)
        self.assertIn("width: 194mm", content)
        self.assertIn("<svg", content)
        self.assertNotIn("<script", content)

    def test_statistics_layout(self):
        content = render_daily_html(self._model(), online_map=False)
        self.assertIn("Max. Geschw.", content)
        self.assertIn('class="total-row"', content)
        self.assertIn("Gesamt", content)

    def test_entries_are_rendered(self):
        content = render_daily_html(self._model(), online_map=False)
        self.assertIn("Motor an", content)
        self.assertIn("Hafen verlassen", content)


if __name__ == "__main__":
    unittest.main()
