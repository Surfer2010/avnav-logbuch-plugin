# Actions

## Ziel

Buttons erzeugen keine Events direkt.

Sie lösen Aktionen aus.

---

# Ablauf

```text
Button

↓

Action

↓

Popup

↓

Event

↓

JSONL
```

---

# Beispiel

Motor aus

↓

Action

↓

Motorstunden-Popup

↓

motor_off

↓

Event speichern

---

# Action Definition

Langfristig sollen Actions konfigurierbar werden.

Beispiel:

```json
{
  "id": "motor_off",
  "label": "Motor aus",
  "event": "motor_off",
  "popup": "motorHours"
}
```

---

# Actiontypen

## Sofortaktion

Kein Dialog.

Beispiel:

- Anker auf

---

## Aktion mit Popup

Beispiel:

- Motor aus
- Segel gesetzt

---

## Freie Ereignisse

Unabhängig von Zuständen.

Beispiele:

- Wetter
- Delfine
- Reparatur
- Crewwechsel
- Foto
- Landgang

---

# Vorteile

Neue Aktionen können ergänzt werden, ohne die Event Engine zu verändern.

Das reduziert Sonderfälle und verbessert die Erweiterbarkeit.