# Notification System Design

## Types of Notifications

### System Notifications
- Event cancelled
- Event created
- Event reminder

### Player Notifications
- Promoted to playing
- Moved to waiting
- Removed from event

---

## Delivery Channels

- WhatsApp (primary)
- In-app (fallback)
- Email (optional)

---

## Rules

- Must be asynchronous (non-blocking)
- Must log delivery status
- Retry on failure (1–2 times)

---

## Future AI Role

AI can:
- Draft message tone
- Personalise messages
- Summarise updates