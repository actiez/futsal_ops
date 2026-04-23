# Create Event Flow

## Principle

AI assists in collecting event details but MUST NOT create event until all required fields are complete and confirmed.

---

## Required Fields

- location
- date
- start_time
- duration
- amount_payable
- playing_slots
- waiting_slots
- backup_slots

---

## Flow

1. Admin initiates event creation
2. AI extracts available fields
3. AI identifies missing required fields
4. AI prompts admin for missing details
5. Repeat until all fields are complete
6. AI presents full summary
7. Admin confirms
8. Event is created

---

## Rules

- No required field can be skipped
- No event is created with incomplete data
- Defaults only allowed if explicitly configured
- Always require final confirmation before creation