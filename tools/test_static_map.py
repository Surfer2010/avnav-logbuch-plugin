#!/usr/bin/env python3

import unittest
from datetime import datetime, timezone

from renderers.render_static_map import (
    choose_zoom,
    lat_to_world_y,
    lon_to_world_x,
    project,
    render_static_map,
    world_x_to_lon,
    world_y_to_lat,
)


class StaticMapTests(unittest.TestCase):
    def test_projection_round_trip(self):
        zoom = 9
        lat = 54.1234
        lon = 10.5678
        x = lon_to_world_x(lon, zoom)
        y = lat_to_world_y(lat, zoom)
        self.assertAlmostEqual(world_x_to_lon(x, zoom), lon, places=6)
        self.assertAlmostEqual(world_y_to_lat(y, zoom), lat, places=6)

    def test_zoom_fits_bounds(self):
        bounds = {"min_lat": 54.0, "max_lat": 54.1, "min_lon": 10.0, "max_lon": 10.2}
        zoom = choose_zoom(bounds, 1200, 700)
        self.assertGreaterEqual(zoom, 4)
        self.assertLessEqual(zoom, 16)

    def test_offline_svg_contains_track_and_markers(self):
        points = [
            {"lat": 54.0, "lon": 10.0, "timestamp": datetime(2026, 6, 1, 10, 0, tzinfo=timezone.utc)},
            {"lat": 54.02, "lon": 10.03, "timestamp": datetime(2026, 6, 1, 10, 10, tzinfo=timezone.utc)},
            {"lat": 54.04, "lon": 10.06, "timestamp": datetime(2026, 6, 1, 10, 20, tzinfo=timezone.utc)},
        ]
        model = {
            "track_points": points,
            "segment_groups": [
                {"category": "motor", "points": points[:2]},
                {"category": "sail", "points": points[1:]},
            ],
            "anchors": [{"lat": 54.04, "lon": 10.06}],
            "notes": [{"lat": 54.02, "lon": 10.03}],
        }
        svg = render_static_map(model, online=False)
        self.assertIn("<svg", svg)
        self.assertIn("Offline-Darstellung ohne Kartenhintergrund", svg)
        self.assertIn("#e46b2e", svg)
        self.assertIn("#1666b1", svg)
        self.assertIn("Ankerplatz 1", svg)
        self.assertIn("Logbucheintrag 1", svg)
        self.assertIn(">S<", svg)
        self.assertIn(">Z<", svg)


if __name__ == "__main__":
    unittest.main()
