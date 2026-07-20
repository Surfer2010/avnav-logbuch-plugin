#!/usr/bin/env python3

"""Static SVG map renderer for offline-capable HTML exports.

The renderer has no mandatory third-party dependencies. It can optionally
retrieve raster tiles with urllib, cache them locally, and embed them as
base64 PNG images. If tiles are unavailable, it renders the track on a
structured blue chart-like background.
"""

import base64
import html
import math
import os
import re
import urllib.error
import urllib.request
from pathlib import Path
from xml.etree import ElementTree as ET

TILE_SIZE = 256
DEFAULT_WIDTH = 1500
DEFAULT_HEIGHT = 760
DEFAULT_MIN_ZOOM = 4
DEFAULT_MAX_ZOOM = 16
DEFAULT_MAX_TILES = 48
DEFAULT_TILE_TIMEOUT = 2.5
USER_AGENT = "avnav-logbuch-plugin static-map-export"

CATEGORY_STYLES = {
    "motor": {"stroke": "#e46b2e", "label": "Motor"},
    "sail": {"stroke": "#1666b1", "label": "Segel"},
    "unknown": {"stroke": "#6f7782", "label": "Unbekannt"},
}


def _escape(value):
    return html.escape(str(value), quote=True)


def lon_to_world_x(lon, zoom):
    return (float(lon) + 180.0) / 360.0 * (2 ** zoom) * TILE_SIZE


def lat_to_world_y(lat, zoom):
    lat = max(-85.05112878, min(85.05112878, float(lat)))
    lat_rad = math.radians(lat)
    return (
        1.0
        - math.log(math.tan(lat_rad) + 1.0 / math.cos(lat_rad)) / math.pi
    ) / 2.0 * (2 ** zoom) * TILE_SIZE


def world_x_to_lon(x, zoom):
    return float(x) / ((2 ** zoom) * TILE_SIZE) * 360.0 - 180.0


def world_y_to_lat(y, zoom):
    value = math.pi * (1.0 - 2.0 * float(y) / ((2 ** zoom) * TILE_SIZE))
    return math.degrees(math.atan(math.sinh(value)))


def _bounds_from_model(model):
    points = model.get("track_points") or []
    coordinates = [(point.get("lat"), point.get("lon")) for point in points]
    for event in (model.get("anchors") or []) + (model.get("notes") or []):
        coordinates.append((event.get("lat"), event.get("lon")))
    coordinates = [
        (float(lat), float(lon))
        for lat, lon in coordinates
        if lat is not None and lon is not None
    ]
    if not coordinates:
        return None
    return {
        "min_lat": min(lat for lat, _ in coordinates),
        "max_lat": max(lat for lat, _ in coordinates),
        "min_lon": min(lon for _, lon in coordinates),
        "max_lon": max(lon for _, lon in coordinates),
    }


def _expand_bounds(bounds, minimum_span_degrees=0.01, padding_ratio=0.12):
    if bounds is None:
        return None
    min_lat = bounds["min_lat"]
    max_lat = bounds["max_lat"]
    min_lon = bounds["min_lon"]
    max_lon = bounds["max_lon"]
    lat_span = max(max_lat - min_lat, minimum_span_degrees)
    lon_span = max(max_lon - min_lon, minimum_span_degrees)
    lat_mid = (min_lat + max_lat) / 2.0
    lon_mid = (min_lon + max_lon) / 2.0
    lat_span *= 1.0 + 2.0 * padding_ratio
    lon_span *= 1.0 + 2.0 * padding_ratio
    return {
        "min_lat": max(-85.0, lat_mid - lat_span / 2.0),
        "max_lat": min(85.0, lat_mid + lat_span / 2.0),
        "min_lon": max(-180.0, lon_mid - lon_span / 2.0),
        "max_lon": min(180.0, lon_mid + lon_span / 2.0),
    }


def choose_zoom(bounds, width, height, min_zoom=DEFAULT_MIN_ZOOM, max_zoom=DEFAULT_MAX_ZOOM):
    if bounds is None:
        return min_zoom
    for zoom in range(max_zoom, min_zoom - 1, -1):
        x1 = lon_to_world_x(bounds["min_lon"], zoom)
        x2 = lon_to_world_x(bounds["max_lon"], zoom)
        y1 = lat_to_world_y(bounds["max_lat"], zoom)
        y2 = lat_to_world_y(bounds["min_lat"], zoom)
        if abs(x2 - x1) <= width and abs(y2 - y1) <= height:
            return zoom
    return min_zoom


def _viewport(bounds, width, height, zoom):
    x1 = lon_to_world_x(bounds["min_lon"], zoom)
    x2 = lon_to_world_x(bounds["max_lon"], zoom)
    y1 = lat_to_world_y(bounds["max_lat"], zoom)
    y2 = lat_to_world_y(bounds["min_lat"], zoom)
    span_x = max(1.0, x2 - x1)
    span_y = max(1.0, y2 - y1)
    scale = min(width / span_x, height / span_y)
    draw_width = span_x * scale
    draw_height = span_y * scale
    offset_x = (width - draw_width) / 2.0 - x1 * scale
    offset_y = (height - draw_height) / 2.0 - y1 * scale
    return {
        "scale": scale,
        "offset_x": offset_x,
        "offset_y": offset_y,
        "world_min_x": x1,
        "world_max_x": x2,
        "world_min_y": y1,
        "world_max_y": y2,
    }


def project(lat, lon, zoom, viewport):
    x = lon_to_world_x(lon, zoom) * viewport["scale"] + viewport["offset_x"]
    y = lat_to_world_y(lat, zoom) * viewport["scale"] + viewport["offset_y"]
    return x, y


def _parse_chart_xml(path):
    result = []
    if not path:
        return result
    path = Path(path)
    if not path.exists():
        return result
    try:
        root = ET.parse(path).getroot()
    except (ET.ParseError, OSError):
        return result
    for tile_map in root.findall(".//TileMap"):
        href = (tile_map.get("href") or "").strip()
        if not href:
            continue
        result.append({
            "title": (tile_map.get("title") or "Karte").strip(),
            "href": href.replace("http://", "https://"),
            "minzoom": int(tile_map.get("minzoom") or DEFAULT_MIN_ZOOM),
            "maxzoom": int(tile_map.get("maxzoom") or DEFAULT_MAX_ZOOM),
        })
    return result


def _default_layers():
    return [
        {"title": "OSM", "href": "https://a.tile.openstreetmap.org/", "minzoom": 4, "maxzoom": 19},
        {"title": "OpenSeaMap", "href": "https://tiles.openseamap.org/seamark/", "minzoom": 6, "maxzoom": 18},
    ]


def _tile_path(cache_dir, layer_title, zoom, x, y):
    safe_title = re.sub(r"[^A-Za-z0-9_.-]+", "_", layer_title or "layer")
    return Path(cache_dir) / safe_title / str(zoom) / str(x) / f"{y}.png"


def _read_tile(cache_dir, layer, zoom, x, y, online, timeout):
    cache_path = _tile_path(cache_dir, layer["title"], zoom, x, y) if cache_dir else None
    if cache_path and cache_path.exists():
        try:
            return cache_path.read_bytes()
        except OSError:
            pass
    if not online:
        return None
    url = f"{layer['href'].rstrip('/')}/{zoom}/{x}/{y}.png"
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            data = response.read()
            content_type = response.headers.get("Content-Type", "")
            if not data or "image" not in content_type:
                return None
    except (urllib.error.URLError, TimeoutError, OSError):
        return None
    if cache_path:
        try:
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            temporary = cache_path.with_suffix(".tmp")
            temporary.write_bytes(data)
            os.replace(temporary, cache_path)
        except OSError:
            pass
    return data


def _tile_range(bounds, zoom):
    max_index = (2 ** zoom) - 1
    min_x = max(0, int(math.floor(lon_to_world_x(bounds["min_lon"], zoom) / TILE_SIZE)))
    max_x = min(max_index, int(math.floor(lon_to_world_x(bounds["max_lon"], zoom) / TILE_SIZE)))
    min_y = max(0, int(math.floor(lat_to_world_y(bounds["max_lat"], zoom) / TILE_SIZE)))
    max_y = min(max_index, int(math.floor(lat_to_world_y(bounds["min_lat"], zoom) / TILE_SIZE)))
    return min_x, max_x, min_y, max_y


def _svg_background(width, height):
    lines = [
        '<defs>',
        '<linearGradient id="seaGradient" x1="0" y1="0" x2="0" y2="1">',
        '<stop offset="0%" stop-color="#d8eef8"/>',
        '<stop offset="100%" stop-color="#b9dceb"/>',
        '</linearGradient>',
        '<pattern id="seaGrid" width="70" height="70" patternUnits="userSpaceOnUse">',
        '<path d="M 70 0 L 0 0 0 70" fill="none" stroke="#6fa8bf" stroke-width="1" opacity="0.28"/>',
        '<path d="M 35 0 V70 M0 35 H70" fill="none" stroke="#8ab9ca" stroke-width="0.6" opacity="0.20"/>',
        '</pattern>',
        '<filter id="trackShadow" x="-20%" y="-20%" width="140%" height="140%">',
        '<feDropShadow dx="0" dy="2" stdDeviation="2" flood-color="#12394b" flood-opacity="0.35"/>',
        '</filter>',
        '</defs>',
        f'<rect width="{width}" height="{height}" fill="url(#seaGradient)"/>',
        f'<rect width="{width}" height="{height}" fill="url(#seaGrid)"/>',
    ]
    for index in range(6):
        y = 70 + index * 115
        lines.append(
            f'<path d="M0 {y} C220 {y-18}, 430 {y+20}, 650 {y} S1080 {y-18}, {width} {y+4}" '
            'fill="none" stroke="#ffffff" stroke-width="3" opacity="0.16"/>'
        )
    return "".join(lines)


def _svg_tile_images(bounds, zoom, viewport, layers, cache_dir, online, timeout, max_tiles):
    min_x, max_x, min_y, max_y = _tile_range(bounds, zoom)
    tile_count = (max_x - min_x + 1) * (max_y - min_y + 1)
    if tile_count <= 0 or tile_count > max_tiles:
        return "", 0, tile_count
    images = []
    loaded = 0
    for layer in layers:
        if zoom < layer.get("minzoom", 0) or zoom > layer.get("maxzoom", 99):
            continue
        for x in range(min_x, max_x + 1):
            for y in range(min_y, max_y + 1):
                data = _read_tile(cache_dir, layer, zoom, x, y, online, timeout)
                if not data:
                    continue
                world_x = x * TILE_SIZE
                world_y = y * TILE_SIZE
                svg_x = world_x * viewport["scale"] + viewport["offset_x"]
                svg_y = world_y * viewport["scale"] + viewport["offset_y"]
                svg_size = TILE_SIZE * viewport["scale"]
                encoded = base64.b64encode(data).decode("ascii")
                images.append(
                    f'<image x="{svg_x:.2f}" y="{svg_y:.2f}" width="{svg_size:.2f}" height="{svg_size:.2f}" '
                    f'href="data:image/png;base64,{encoded}" preserveAspectRatio="none"/>'
                )
                loaded += 1
    return "".join(images), loaded, tile_count


def _polyline(points, category, zoom, viewport):
    coords = []
    for point in points:
        if point.get("lat") is None or point.get("lon") is None:
            continue
        x, y = project(point["lat"], point["lon"], zoom, viewport)
        coords.append(f"{x:.1f},{y:.1f}")
    if len(coords) < 2:
        return ""
    style = CATEGORY_STYLES.get(category, CATEGORY_STYLES["unknown"])
    return (
        f'<polyline points="{" ".join(coords)}" fill="none" stroke="#ffffff" stroke-width="12" '
        'stroke-linejoin="round" stroke-linecap="round" opacity="0.75"/>'
        f'<polyline points="{" ".join(coords)}" fill="none" stroke="{style["stroke"]}" stroke-width="7" '
        'stroke-linejoin="round" stroke-linecap="round" filter="url(#trackShadow)"/>'
    )


def _circle_marker(x, y, fill, label, title):
    return (
        f'<g><title>{_escape(title)}</title>'
        f'<circle cx="{x:.1f}" cy="{y:.1f}" r="15" fill="#ffffff" stroke="#17384a" stroke-width="3"/>'
        f'<circle cx="{x:.1f}" cy="{y:.1f}" r="10" fill="{fill}"/>'
        f'<text x="{x:.1f}" y="{y+5:.1f}" text-anchor="middle" font-size="13" font-weight="700" fill="#ffffff">{_escape(label)}</text>'
        '</g>'
    )


def _anchor_marker(x, y, title):
    return (
        f'<g transform="translate({x:.1f},{y:.1f})"><title>{_escape(title)}</title>'
        '<circle r="18" fill="#ffffff" stroke="#17384a" stroke-width="3"/>'
        '<path d="M0 -12 V10 M-6 -7 H6 M-11 5 C-8 14,8 14,11 5 M-11 5 L-15 1 M11 5 L15 1" '
        'fill="none" stroke="#17384a" stroke-width="3" stroke-linecap="round"/>'
        '</g>'
    )


def _note_marker(x, y, title):
    return (
        f'<g transform="translate({x:.1f},{y:.1f})"><title>{_escape(title)}</title>'
        '<circle r="17" fill="#ffffff" stroke="#17384a" stroke-width="3"/>'
        '<path d="M-8 -9 H8 V6 H1 L-5 11 V6 H-8 Z" fill="#f1b44c" stroke="#17384a" stroke-width="2"/>'
        '</g>'
    )


def _legend(width, height, background_available):
    x = 24
    y = height - 62
    items = []
    current_x = x + 16
    for category in ("sail", "motor", "unknown"):
        style = CATEGORY_STYLES[category]
        items.append(f'<line x1="{current_x}" y1="{y+25}" x2="{current_x+42}" y2="{y+25}" stroke="{style["stroke"]}" stroke-width="7" stroke-linecap="round"/>')
        items.append(f'<text x="{current_x+52}" y="{y+31}" font-size="20" fill="#17384a">{style["label"]}</text>')
        current_x += 155
    map_text = "Kartenhintergrund eingebettet" if background_available else "Offline-Darstellung ohne Kartenhintergrund"
    items.append(f'<text x="{width-24}" y="{y+31}" text-anchor="end" font-size="17" fill="#355d70">{_escape(map_text)}</text>')
    return (
        f'<rect x="{x}" y="{y}" width="{width-2*x}" height="48" rx="10" fill="#ffffff" opacity="0.88"/>'
        + "".join(items)
    )


def render_map_placeholder(width=DEFAULT_WIDTH, height=DEFAULT_HEIGHT, message="Keine Trackdaten verfügbar"):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" '
        f'aria-label="{_escape(message)}">'
        f'{_svg_background(width, height)}'
        f'<text x="{width/2:.0f}" y="{height/2-10:.0f}" text-anchor="middle" font-size="36" font-weight="700" fill="#17384a">Kartenansicht</text>'
        f'<text x="{width/2:.0f}" y="{height/2+40:.0f}" text-anchor="middle" font-size="24" fill="#355d70">{_escape(message)}</text>'
        '</svg>'
    )


def render_static_map(
    model,
    width=DEFAULT_WIDTH,
    height=DEFAULT_HEIGHT,
    cache_dir=None,
    chart_xml=None,
    online=True,
    timeout=DEFAULT_TILE_TIMEOUT,
    max_tiles=DEFAULT_MAX_TILES,
):
    """Return a self-contained SVG string.

    The result is valid without Internet access. Raster tiles are optional;
    all vector overlays and the fallback background are always embedded.
    """
    bounds = _expand_bounds(_bounds_from_model(model))
    if bounds is None:
        return render_map_placeholder(width, height)
    zoom = choose_zoom(bounds, width, height)
    viewport = _viewport(bounds, width, height, zoom)
    layers = _parse_chart_xml(chart_xml) or _default_layers()
    tile_images, loaded_tiles, requested_tiles = _svg_tile_images(
        bounds,
        zoom,
        viewport,
        layers,
        cache_dir,
        online,
        timeout,
        max_tiles,
    )

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
        f'viewBox="0 0 {width} {height}" role="img" aria-label="Statische Karte des Tagetracks">',
        _svg_background(width, height),
    ]
    if tile_images:
        parts.append(f'<g opacity="0.96">{tile_images}</g>')
        parts.append(f'<rect width="{width}" height="{height}" fill="#ffffff" opacity="0.05"/>')

    for group in model.get("segment_groups") or []:
        parts.append(_polyline(group.get("points") or [], group.get("category") or "unknown", zoom, viewport))

    track_points = model.get("track_points") or []
    if track_points:
        start = track_points[0]
        end = track_points[-1]
        sx, sy = project(start["lat"], start["lon"], zoom, viewport)
        ex, ey = project(end["lat"], end["lon"], zoom, viewport)
        parts.append(_circle_marker(sx, sy, "#2b9a55", "S", "Start"))
        parts.append(_circle_marker(ex, ey, "#c63f3f", "Z", "Ziel"))

    for index, event in enumerate(model.get("anchors") or [], start=1):
        x, y = project(event["lat"], event["lon"], zoom, viewport)
        parts.append(_anchor_marker(x, y, f"Ankerplatz {index}"))
    for index, event in enumerate(model.get("notes") or [], start=1):
        x, y = project(event["lat"], event["lon"], zoom, viewport)
        parts.append(_note_marker(x, y, f"Logbucheintrag {index}"))

    parts.append(_legend(width, height, loaded_tiles > 0))
    if requested_tiles > max_tiles:
        parts.append(
            f'<text x="{width-24}" y="28" text-anchor="end" font-size="16" fill="#355d70">'
            f'Kartenhintergrund ausgelassen: {requested_tiles} Kacheln überschreiten das Limit {max_tiles}</text>'
        )
    parts.append('</svg>')
    return "".join(parts)
