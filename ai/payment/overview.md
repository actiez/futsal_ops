# Payment System Overview

## Purpose

The payment system manages:
- payment calculation
- player-level payment tracking
- QR-based payment requests
- proof submission
- admin verification
- reconciliation support

## Principles

- AI suggests, system enforces, admin decides
- No automatic payment confirmation in v1
- All payments must be traceable via transaction reference
- Payment is tied to final event participation

## Flow

Event ends
→ final players locked
→ payment records created
→ reference generated
→ QR generated
→ player pays
→ player submits proof
→ admin verifies
→ payment marked as paid