# WhatsApp UX – Player

## Principle

- Group chat = broadcast only  
- Private message (PM) = all actions  
- No actions should be handled in group chat  

---

## Group Broadcast Message

⚽ FUTSAL GAME

📅 Sunday, 7:00 PM – 9:00 PM  
📍 Keat Hong Gardens  
💰 $2 per pax  

To join or check your status, please PM me.

---

## First PM Response

Hi! I can help you with this game.

You can say:
- Join game
- Check status
- Leave game

---

## Join Flow

User:
"Join game"

AI:
You're joining:

📅 Sunday 7PM  
📍 Keat Hong  

Confirm?

Reply:
YES / NO

---

## Join Result

### Playing
✅ You're in the game (Playing)

### Waiting
⏳ You're on the waiting list  
Position: #2

### Pending
🕒 Your status is pending  

The slots may be pending final confirmation or you are waiting to move into the waiting list when a slot opens.

---

## Leave Flow

User:
"Leave game"

Step 1:
Are you sure you want to leave this game?

Reply:
YES / NO

Step 2:
This action cannot be undone.

Confirm leaving?

Reply:
CONFIRM / CANCEL

---

## Status Flow

User:
"Status"

### Playing
✅ You're in the game (Playing)

### Waiting
⏳ Waiting list  
Position: #3

### Pending
🕒 Status: Pending  

The slots may be pending final confirmation or you are waiting to move into the waiting list when a slot opens.

---

## Fallback

I didn’t catch that.

You can:
- Join game
- Leave game
- Check status