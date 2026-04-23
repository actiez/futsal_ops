# Recurring Event Policy

## Rule
Recurring events are OFF by default.

## Activation
Recurring events only happen when an admin explicitly enables recurrence.

Example admin commands:
- Create recurring event
- Make this a weekly game

## Lifecycle
1. System creates event
2. Notification / join link is sent
3. Players register
4. Event runs
5. Event ends
6. Lifecycle engine checks recurrence
7. If recurrence is enabled and valid, the next event is created

## Safeguards
- Do not create duplicate next events
- Cancelled events should not continue recurrence by default
- Admin can stop recurrence at any time
- Recurrence should only trigger after event completion/end

## AI Role
AI may configure and trigger recurrence through approved backend functions, but recurrence logic remains deterministic and backend-controlled.