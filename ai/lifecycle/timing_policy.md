# Lifecycle Timing Policy

## Rule

All automatic lifecycle actions must be delayed by a buffer period.

## Default Buffer

+3 hours after event end time

## Applies To

- Recurring event creation
- Post-event processing

## Purpose

- Prevent duplicate triggers
- Allow admin intervention window
- Avoid race conditions

## Rule

No lifecycle automation should run immediately at event end