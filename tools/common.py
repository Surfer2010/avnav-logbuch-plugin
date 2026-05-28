#!/usr/bin/env python3
"""
Gemeinsame Hilfsfunktionen für AVNav Logbuch Tools.

Ziel:
- einheitliche Pfaderkennung
- weniger feste Pfade in einzelnen Scripts
- gleiche Nutzung auf Live-System und Test-LXC

Priorität:
1. expliziter CLI-Pfad
2. Umgebungsvariable AVNAV_DATA_DIR
3. /home/pi/avnav/data
4. /var/lib/avnav
"""

import os
from pathlib import Path


DEFAULT_PI_AVNAV_DATA = Path("/home/pi/avnav/data")
DEFAULT_DEBIAN_AVNAV_DATA = Path("/var/lib/avnav")


def detect_avnav_data_dir(cli_value=None):
    """
    AVNav-Datenverzeichnis erkennen.

    cli_value:
        Wert aus --avnav-data.
        Wenn gesetzt, hat dieser immer Vorrang.
    """

    if cli_value:
        return Path(cli_value).expanduser().resolve()

    env_value = os.environ.get("AVNAV_DATA_DIR")

    if env_value:
        return Path(env_value).expanduser().resolve()

    if DEFAULT_PI_AVNAV_DATA.exists():
        return DEFAULT_PI_AVNAV_DATA.resolve()

    if DEFAULT_DEBIAN_AVNAV_DATA.exists():
        return DEFAULT_DEBIAN_AVNAV_DATA.resolve()

    raise FileNotFoundError(
        "AVNav data directory not found. "
        "Use --avnav-data or set AVNAV_DATA_DIR."
    )


def get_logbook_dir(avnav_data_dir):
    return Path(avnav_data_dir) / "logbook"


def get_tracks_dir(avnav_data_dir):
    return Path(avnav_data_dir) / "tracks"


def get_plugins_dir(avnav_data_dir):
    return Path(avnav_data_dir) / "plugins"


def print_detected_paths(avnav_data_dir):
    """
    Diagnoseausgabe für CLI-Tools.
    """

    avnav_data_dir = Path(avnav_data_dir)

    print(f"AVNav data: {avnav_data_dir}")
    print(f"Logbook:    {get_logbook_dir(avnav_data_dir)}")
    print(f"Tracks:     {get_tracks_dir(avnav_data_dir)}")
    print(f"Overlays:   {get_overlays_dir(avnav_data_dir)}")
    print(f"Plugins:    {get_plugins_dir(avnav_data_dir)}")


def get_overlays_dir(avnav_data_dir):
    return Path(avnav_data_dir) / "overlays"
