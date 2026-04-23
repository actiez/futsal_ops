# Auto Event Creation

## Purpose
Automatically create the next event when the current event ends.

---

## Trigger

Event reaches:
- end_datetime < now
- status = completed

---

## Preconditions

- Event is not cancelled
- Event has minimum participation (optional rule)
- System setting: auto_create_enabled = true

---

## Creation Logic

New event should inherit:

- location
- duration (e.g. 2 hours)
- playing_slots
- waiting_slots
- amount_payable

---

## Time Logic

Default:
- next event = +7 days same weekday & time

Example:
Sunday 7PM → next Sunday 7PM

---

## Safety Rules

- Do NOT create duplicate events
- Check if similar event already exists within same time window
- Allow admin override

---

## Admin Control

Admin can:
- enable / disable auto-create
- edit template settings

---

## AI Role (Future)

Admin:
"Create weekly recurring event"

AI:
→ enables auto_create flag
→ sets recurrence pattern