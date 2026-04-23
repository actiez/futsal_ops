# Transaction Reference

## Principle

Each player × event must have a unique transaction reference.

## Purpose

- enable deterministic reconciliation
- avoid ambiguity
- link payment directly to player

## Rules

- must be unique
- generated before QR creation
- stored in payment record
- included in QR payload

## Matching Priority

1. reference (primary)
2. amount
3. timestamp