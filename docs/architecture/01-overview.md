# System Overview

## Ziel

Das Plugin dient zur Erfassung nautischer Ereignisse während eines Törns.

Es speichert keine kontinuierlichen Trackdaten, sondern ausschließlich Ereignisse.

---

# Gesamtarchitektur

```text
Benutzer

│

▼

Actions

│

▼

Popup Framework

│

▼

Event Engine

│

▼

Normalisierung

│

▼

JSONL

│

├──────────────┐

▼              ▼

InfluxDB    Export Engine

               │

       ┌───────┼────────────┐

       ▼       ▼            ▼

      KMZ   Markdown       CSV
```

---

# Komponenten

## Benutzeroberfläche

- Statusbuttons
- freie Ereignisse
- Popup-Dialoge
- Exporte

---

## Event Engine

Erzeugt strukturierte Events.

Alle Events besitzen dasselbe Schema.

---

## JSONL

Primäre Speicherung.

Ein Event pro Zeile.

Keine Datenbank notwendig.

---

## Export Engine

Verarbeitet ausschließlich normalisierte Events.

Exportiert:

- KMZ
- Markdown
- CSV

Später:

- PDF
- HTML
- EPUB

---

## Trackdaten

Trackdaten stammen nicht aus dem Logbuch.

Sie werden aus:

- NMEA
- GPX
- AVT

bezogen.

---

## Datenfluss

```text
Benutzer

↓

Action

↓

Popup

↓

Event

↓

Normalisierung

↓

JSONL

↓

Export
```