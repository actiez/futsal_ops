# Ambiguity Handling

AI must not assume missing or unclear information.

## Common Ambiguities

- Multiple upcoming events
- Missing event time/date
- Missing location
- Vague requests ("that game", "my game")

---

## Handling Strategy

1. Detect intent
2. Identify missing fields
3. Ask ONE clarifying question at a time
4. Wait for response
5. Only proceed when complete

---

## Example

User:
"I coming"

AI:
"Which event are you referring to?
1. Sunday 7PM – CCK
2. Tuesday 9PM – Jurong"

---

## Rules

- Never guess silently
- Always confirm before execution
- Keep questions simple and short