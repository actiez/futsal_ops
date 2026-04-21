# Player Workflow

## 1. Access Game
- Player opens unique event link
- If not logged in → redirect to login
- After login → return to event page

---

## 2. Join Game
- Player clicks "Join"
- System creates registration

### Internal Assignment Rules
- Core → auto assigned to PLAYING (if slots available)
- Naughty → auto assigned to BACKUP
- Others → assigned to INTERESTED

---

## 3. Status Visibility (IMPORTANT)
Player sees:
- Pending
- Confirmed

Player does NOT see:
- Waiting
- Backup
- Internal prioritisation logic

---

## 4. Slot Allocation (Admin/System)
Admin or system moves players between:
- Playing
- Waiting
- Backup

---

## 5. Leave Game
- Player clicks "Leave"
- Confirmation required
- Registration removed

---

## 6. Event Completion
- Event automatically marked as completed after end time
- No manual finalisation required