# Event Reference Resolution

Defines how AI identifies events from user input.

## Resolution Priority

1. Registration token (highest accuracy)
2. Exact event ID (internal use)
3. Date/time matching
4. Location matching
5. Fuzzy text matching

---

## Examples

User Input → Resolution

"Sunday game"
→ Match event by nearest Sunday

"tomorrow 7pm"
→ Match by datetime

"CCK game"
→ Match by location

"my next game"
→ Match next registered event

---

## Multiple Matches

If more than one match:
→ Ask clarification

Example:
"I found 2 events:
1. Sunday 7PM – CCK
2. Sunday 9PM – Hougang
Which one?"

---

## No Match

→ Inform user:
"No matching event found. Please check details."

---

## Rules

- Never auto-pick if multiple matches
- Always confirm final selection before action