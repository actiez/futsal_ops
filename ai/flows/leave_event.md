# Leave Event Flow

1. User:
   "I can't make it"

2. AI:
   Detect LEAVE_EVENT

3. AI:
   "Are you sure you want to leave?"

4. User confirms

5. AI:
   leave_event(user, event_id)

6. Backend:
   Rebalance slots

7. AI confirms:
   "You have left the event"