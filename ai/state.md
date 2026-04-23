# Conversation State Model

AI interactions are stateful. Each user may be in a temporary conversation state.

## State Structure

- user_id
- state_name
- context_data (JSON)
- expected_input
- expires_at

## Example States

### JOIN_CONFIRMATION
User intends to join an event and is awaiting confirmation

context_data:
- event_id
- token

expected_input:
- yes / no

---

### LEAVE_CONFIRMATION
User intends to leave an event and must confirm

context_data:
- event_id

expected_input:
- yes / no

---

### VERIFICATION_PENDING
User must answer a verification question

context_data:
- question
- expected_answer (hashed or rule-based)

expected_input:
- free text

---

### CREATE_EVENT_DRAFT
Admin is providing event details step-by-step

context_data:
- partial event fields

expected_input:
- missing fields

---

## Expiry Rules

- Default expiry: 5–10 minutes
- After expiry:
  → state is cleared
  → user must restart flow

---

## Rules

- Only ONE active state per user
- New intent overrides old state
- Confirmation must match active state