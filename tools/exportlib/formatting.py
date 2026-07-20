#!/usr/bin/env python3

import html
from datetime import datetime


def parse_datetime(value):
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except Exception:
        return None


def escape(value):
    return html.escape(str(value), quote=True)


def format_hms(seconds):
    seconds = int(max(0, seconds or 0))
    return f"{seconds // 3600:02d}:{(seconds % 3600) // 60:02d}:{seconds % 60:02d}"


def format_duration_short(seconds):
    seconds = int(max(0, seconds or 0))
    hours, rest = divmod(seconds, 3600)
    minutes = rest // 60
    return f"{hours}:{minutes:02d} h"
