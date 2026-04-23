# Custom Report System

## Design Principles
- No raw SQL
- No direct DB queries
- Use structured query schema

## Query Spec Format

{
  "intent": "GET_CUSTOM_REPORT",
  "entity": "players",
  "metric": "count",
  "filters": {
    "player_type": "core",
    "played_on": "today"
  },
  "group_by": null
}

## Example

User:
"How many core players played today?"

AI converts to structured query → tool executes → formatted response returned