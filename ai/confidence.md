# Intent Confidence Policy

Defines how AI reacts based on confidence score.

## Thresholds

- ≥ 0.90 → Proceed to confirmation
- 0.70 – 0.89 → Ask clarification
- < 0.70 → Fallback help message

## Examples

"I coming" → JOIN_EVENT (0.95) → proceed  
"maybe join later" → unclear (0.65) → clarify  
"yo bro whats up" → HELP (fallback)

## Rule

AI must NEVER execute action below 0.90 confidence