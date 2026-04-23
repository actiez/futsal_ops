# Join Event Flow

1. User sends:
   "I coming"

2. AI detects:
   JOIN_EVENT

3. AI checks:
   - User registered?
   - Token valid?

4. AI response:
   "Do you want to join this event?"

5. User confirms

6. AI calls:
   join_event_by_token(user, token)

7. Backend assigns status

8. AI responds with:
   - Playing / Waiting / Pending