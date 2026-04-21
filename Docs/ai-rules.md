# AI Rules (Planned)

## Objective
Improve attendance reliability and fairness in slot allocation

---

## Inputs
- Attendance history
- No-show rate
- Last played timestamp
- Player type
- Join timing

---

## Scoring Model (v1)
Each player is assigned a score:

score =
+ reliability_score
- no_show_penalty
+ fairness_bonus (if not played recently)

---

## Output
- Sorted player ranking
- Top players → playing
- Next → waiting
- Remaining → backup

---

## Future Enhancements
- No-show prediction
- Auto overbooking
- Smart promotions
- Player behaviour profiling