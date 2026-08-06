#!/usr/bin/env python3
"""Zeitbehandlung für AVNav-Logbuchexporte.

Gespeicherte Logbuch-Zeitstempel bleiben intern UTC. Eingaben ohne
Zeitzonenangabe werden als lokale Zeit des AVNav-Servers interpretiert.
Für die Darstellung werden Zeitstempel in die lokale Serverzeitzone
umgerechnet.
"""

from datetime import datetime, timezone


def parse_datetime(value):
    """ISO-Zeitangabe lesen und als UTC-Datetime zurückgeben.

    Angaben mit Z oder Offset werden entsprechend umgerechnet.
    Angaben ohne Offset gelten als lokale Zeit des AVNav-Servers.
    """

    text = str(value or "").strip()

    if not text:
        raise ValueError("Zeitangabe fehlt")

    if text.endswith("Z"):
        parsed = datetime.fromisoformat(
            text[:-1] + "+00:00"
        )
    else:
        parsed = datetime.fromisoformat(text)

    if parsed.tzinfo is None:
        # astimezone() interpretiert naive Werte in der lokalen
        # Zeitzone des Servers und berücksichtigt dessen DST-Regeln.
        parsed = parsed.astimezone()

    return parsed.astimezone(timezone.utc)


def parse_range_datetime(value, end=False):
    parsed = parse_datetime(value)

    if end:
        return parsed.replace(
            second=59,
            microsecond=999999,
        )

    return parsed.replace(
        second=0,
        microsecond=0,
    )


def to_local(value):
    """Datetime in die lokale Zeitzone des Servers umrechnen."""

    if value is None:
        return None

    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)

    # Ohne Argument verwendet astimezone() die Serverzeitzone.
    return value.astimezone()


def local_iso(value):
    localized = to_local(value)

    if localized is None:
        return ""

    return localized.isoformat(timespec="seconds")


def local_label(value, pattern="%d.%m.%Y %H:%M"):
    localized = to_local(value)

    if localized is None:
        return ""

    return localized.strftime(pattern)


def local_compact_date(value):
    localized = to_local(value)

    if localized is None:
        return ""

    return localized.strftime("%Y%m%d")
