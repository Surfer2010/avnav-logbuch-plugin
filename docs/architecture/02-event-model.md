# Event Model

## Ziel

Alle Ereignisse besitzen ein gemeinsames Schema.

---

# Schema

```json
{
  "schema_version": 1,
  "id": "...",
  "timestamp": "...",
  "event_type": "...",
  "text": "...",
  "lat": 0,
  "lon": 0,
  "position_source": "live",
  "sog": 0,
  "cog": 0,
  "heading": 0,
  "state": {},
  "details": {},
  "source": "avnav-logbuch-plugin"
}
```

---

# Pflichtfelder

- schema_version
- id
- timestamp
- event_type

---

# Optionale Felder

- text
- lat
- lon
- details

---

# details

Eventabhängige Informationen.

Beispiele:

Motor:

```json
{
  "engine_hours": 333.4
}
```

Segel:

```json
{
  "headsail": "Genua",
  "reef": 1
}
```

Wetter:

```json
{
  "tws": 14,
  "pressure": 1013
}
```

---

# position_source

Mögliche Werte:

- live
- manual
- track_exact
- interpolated
- unknown

---

# Normalisierung

Alle Events werden beim Lesen und Schreiben normalisiert.

Dadurch besitzen alte und neue Logbücher intern dieselbe Struktur.