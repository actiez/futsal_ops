# Rate Limiting Policy

## Limits

- Max 10 messages per minute per user
- Max 3 failed verification attempts

## Actions

- Exceed limit → temporary block (5–10 mins)
- Excessive abuse → require manual intervention

## Purpose

- Prevent spam
- Prevent brute-force verification
- Protect system load