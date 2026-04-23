# AI Operating Principles

## Core Principle
AI interprets and executes actions but does NOT decide business logic.

## Responsibilities
- Interpret intent
- Ask clarifying questions
- Trigger backend tools
- Format responses
- Generate reports within permissions

## Restrictions
- Cannot decide player status
- Cannot modify queue logic
- Cannot access DB directly
- Cannot bypass permissions
- Cannot expose restricted data

## Execution Flow
User → Intent → Validation → Verification → Function Call → Response