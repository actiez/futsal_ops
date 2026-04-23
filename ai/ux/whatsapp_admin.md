# WhatsApp UX – Admin

## Principle

- Admin controls system via AI
- AI collects required data
- No event is created without full details
- All actions require confirmation

---

## Create Event (Initial Request)

Admin:
"Create game Sunday 7pm CCK"

AI:
I can help create the event, but I still need:

- duration
- amount payable
- playing slots
- waiting slots
- backup slots

Please provide the missing details.

---

## Progressive Data Collection

AI should:
- extract known fields
- ask for missing fields
- repeat until complete

---

## Final Confirmation

Please confirm event creation:

📅 Sunday  
🕖 7:00 PM  
📍 Keat Hong Gardens  
⏱ Duration: 2 hours  
💰 Amount payable: $2  
👥 Playing slots: 10  
🕒 Waiting slots: 4  
📌 Backup slots: 4  

Reply:
CONFIRM / CANCEL

---

## After Confirmation

✅ Event created successfully

Next step:
Send to players?

Reply:
YES / NO

---

## Broadcast Approval

AI:
Ready to send event to players:

📅 Sunday 7PM  
📍 CCK  

Reply:
YES / NO

---

## Cancel Event Flow

Admin:
"Cancel this week's game"

AI:
This is part of a recurring event.

Do you want future games to continue?

Reply:
YES (continue)  
NO (stop)

---

## Cancellation Confirmation

Confirm cancellation of this event?

Reply:
CONFIRM / CANCEL

---

## Result

❌ Event cancelled successfully

Players will be notified.