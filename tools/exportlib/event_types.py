#!/usr/bin/env python3

EVENT_TYPES = {
    "motor_on": {
        "label": "Motor an",
        "icon": "motor-on",
        "category": "motor",
    },
    "motor_off": {
        "label": "Motor aus",
        "icon": "motor-off",
        "category": "motor",
    },
    "sail_set": {
        "label": "Segel gesetzt",
        "icon": "sail-set",
        "category": "sail",
    },
    "sail_down": {
        "label": "Segel eingeholt",
        "icon": "sail-down",
        "category": "sail",
    },
    "anchor_down": {
        "label": "Anker ab",
        "icon": "anchor-down",
        "category": "anchor",
    },
    "anchor_up": {
        "label": "Anker auf",
        "icon": "anchor-up",
        "category": "anchor",
    },
    "manual": {
        "label": "Manueller Eintrag",
        "icon": "manual",
        "category": "note",
    },
    "weather": {
        "label": "Wetter",
        "icon": "weather",
        "category": "weather",
    },
    "wildlife": {
        "label": "Tierbeobachtung",
        "icon": "wildlife",
        "category": "observation",
    },
}


def get_event_type(event_type):
    return EVENT_TYPES.get(
        event_type,
        {
            "label": event_type or "Unbekannt",
            "icon": "manual",
            "category": "other",
        },
    )


def get_event_label(event_type):
    return get_event_type(event_type)["label"]


def get_event_icon(event_type):
    return get_event_type(event_type)["icon"]
