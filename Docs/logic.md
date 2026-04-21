# Core Logic

## Player Types
- Core → highest priority
- Regular → standard
- New → lowest priority
- Naughty → restricted (backup only)

---

## Slot Types
- Playing → confirmed players
- Waiting → next in line
- Backup → overflow / low priority

---

## Assignment Rules
1. Core players fill playing slots first
2. Naughty players always go to backup
3. Others remain as interested until moved

---

## Promotion Logic
When a playing slot is freed:
1. Promote from waiting
2. If no waiting → promote from interested

---

## Constraints
- Playing slots are limited
- Waiting slots are limited
- Backup slots are unlimited