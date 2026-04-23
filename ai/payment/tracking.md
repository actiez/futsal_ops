# Payment Tracking

## Purpose
Track payment obligations and payment completion for each event.

## Chargeable Players
Only players in the final playing list are chargeable by default.

## Payment Statuses
- unpaid
- paid
- waived
- cancelled

## Required Data Per Payment Record
- event_id
- user_id
- pricing_mode
- amount_due
- status
- payee_mobile
- reference
- qr_generated
- requested_at
- paid_at
- notes

## Rules
- Payment records are created only after event completion
- Waiting / pending / backup players are not charged by default
- Admin may manually waive payment
- Payment amount is final once event is locked