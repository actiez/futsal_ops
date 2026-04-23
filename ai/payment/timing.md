# Payment Timing

## Rule

Payments are generated only AFTER event completion.

## Flow

1. event ends
2. final playing list is locked
3. payment records are created

## Reason

- avoid incorrect charges
- ensure fairness
- prevent recalculation