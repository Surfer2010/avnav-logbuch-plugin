#!/usr/bin/env python3

import unittest
from datetime import datetime, timezone

from renderers.render_daily_html import render_daily_html


def statistics():
    empty = {
        "distance_nm": 0.0,
        "duration_seconds": 0,
        "max_speed_kn": 0.0,
        "average_speed_kn": 0.0,
    }

    return {
        "sail": dict(empty),
        "motor": dict(empty),
        "total": dict(empty),
        "unknown": dict(empty),
        "counts": {
            "events": 2,
            "anchorages": 0,
            "notes": 2,
        },
    }


def event(timestamp, text):
    return {
        "_timestamp": timestamp,
        "timestamp": timestamp.isoformat(),
        "event_type": "manual",
        "text": text,
        "lat": 54.0,
        "lon": 10.0,
    }


class Issue54ExportDateColumnTest(unittest.TestCase):

    def render(self, events, date_dash):
        model = {
            "date_dash": date_dash,
            "statistics": statistics(),
            "events": events,
            "anchors": [],
            "notes": events,
            "track_points": [],
            "segment_groups": [],
        }

        return render_daily_html(
            model,
            include_map=False,
            online_map=False,
        )

    def test_single_day_has_date_column(self):
        content = self.render(
            [
                event(
                    datetime(
                        2026, 8, 6, 10, 15,
                        tzinfo=timezone.utc,
                    ),
                    "Eintrag 1",
                ),
            ],
            "2026-08-06",
        )

        self.assertIn(
            "<th>Datum</th><th>Zeit</th>",
            content,
        )

        self.assertIn(
            'class="date">06.08.2026</td>',
            content,
        )

    def test_multiple_days_have_date_for_each_entry(self):
        content = self.render(
            [
                event(
                    datetime(
                        2026, 8, 6, 10, 15,
                        tzinfo=timezone.utc,
                    ),
                    "Tag 1",
                ),
                event(
                    datetime(
                        2026, 8, 7, 11, 30,
                        tzinfo=timezone.utc,
                    ),
                    "Tag 2",
                ),
            ],
            "2026-08-06_bis_2026-08-07",
        )

        self.assertIn(
            'class="date">06.08.2026</td>',
            content,
        )

        self.assertIn(
            'class="date">07.08.2026</td>',
            content,
        )

        self.assertEqual(
            content.count("<th>Datum</th>"),
            1,
        )

    def test_empty_table_uses_five_columns(self):
        content = self.render(
            [],
            "2026-08-06",
        )

        self.assertIn(
            'colspan="5"',
            content,
        )


if __name__ == "__main__":
    unittest.main()
