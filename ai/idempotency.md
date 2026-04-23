# Idempotency Rules

## Principle

Same action should not execute multiple times.

## Examples

JOIN_EVENT:
- If already registered → return existing status
- Do NOT create duplicate registration

LEAVE_EVENT:
- If already left → return "already not in event"

## Rule

All tool functions must be idempotent