# Audit Logging

All AI interactions must be logged for debugging and control.

## Log Structure

- user_id
- phone_number
- raw_message
- detected_intent
- confidence_score
- state_name (if any)
- verification_required (true/false)
- verification_passed (true/false)
- function_called
- function_result
- timestamp

---

## Example Log

{
  "user_id": 12,
  "raw_message": "I coming",
  "intent": "JOIN_EVENT",
  "confidence": 0.92,
  "state": "JOIN_CONFIRMATION",
  "function_called": "join_event_by_token",
  "result": "success",
  "timestamp": "2026-04-22T14:30:00"
}

---

## Purpose

- Debug AI decisions
- Trace user actions
- Prevent misuse
- Improve AI training later

---

## Rules

- Log EVERY interaction
- Do not skip failed attempts
- Logs must be immutable