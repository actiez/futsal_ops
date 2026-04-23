# Cancel Event Flow

## Purpose
Allow admin to cancel event and notify all players.

---

## Trigger

Admin action:
- Web UI OR
- AI command: "Cancel this event"

---

## Confirmation (MANDATORY)

Step 1:
"Are you sure you want to cancel this event?"

Step 2:
"This will notify all players and cannot be undone. Confirm?"

---

## Execution

1. Set event.status = cancelled
2. Lock further registrations
3. Trigger notification process

---

## Notification Scope

Notify ALL registered users:
- playing
- waiting
- interested
- backup

---

## Notification Message

Example:

"⚠️ Event Cancelled  
Sunday 7PM @ CCK has been cancelled.  
We apologise for the inconvenience."

---

## Delivery Method

- WhatsApp (future)
- Email (optional)
- In-app notification

---

## Safety Rules

- Prevent duplicate cancellation
- Prevent cancelling completed events