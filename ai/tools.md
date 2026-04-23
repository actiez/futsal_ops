# Tool / Function Layer

## Player Functions
- join_event_by_token(user, token)
- leave_event(user, event_id)
- get_my_status(user, event_id)
- list_my_games(user)

## Admin Functions
- create_event(user, payload)
- get_event_summary(user, event_id)
- draft_event_message(user, event_id, message_type)

## Reporting Functions
- get_core_player_count(user, filters)
- get_players_played_today(user, filters)
- run_custom_report(user, query_spec)