# Confirmation Rules

Defines which actions require confirmation before execution.

## No Confirmation Required

- CHECK_STATUS
- LIST_MY_GAMES
- HELP

---

## Single Confirmation

- JOIN_EVENT
- CREATE_EVENT
- GET_REPORT

Flow:
1. AI asks: "Do you want to proceed?"
2. User confirms
3. Execute action

---

## Double Confirmation (High Risk)

- LEAVE_EVENT
- DELETE / CANCEL EVENT

Flow:
1. AI asks: "Are you sure you want to leave?"
2. User confirms
3. AI asks again: "This action cannot be undone. Confirm?"
4. Execute action

---

## Rules

- Confirmation must match active state
- “yes” without context = ignored
- Expired state = restart confirmation